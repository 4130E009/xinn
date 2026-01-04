import streamlit as st
import random
import time

# ==========================================
# 1. 核心邏輯與工具函式
# ==========================================

def create_deck():
    """ 產生 6 副撲克牌並洗牌 """
    suits = ['♠️', '♥️', '♦️', '♣️']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    # 使用 6 副牌 (* 6)
    deck = [f"{suit} {rank}" for suit in suits for rank in ranks] * 6
    random.shuffle(deck)
    return deck

def calculate_score(hand):
    """ 計算點數 (A 自動切換 1 或 11) """
    score = 0
    aces = 0
    for card in hand:
        rank = card.split()[1]
        if rank in ['J', 'Q', 'K']:
            score += 10
        elif rank == 'A':
            aces += 1
            score += 11
        else:
            score += int(rank)
    
    # 如果爆牌，把 A 當成 1
    while score > 21 and aces > 0:
        score -= 10
        aces -= 1
    return score

def display_cards(hand, hidden=False):
    """ 使用 CSS 繪製漂亮的卡牌 """
    cards_html = ""
    for index, card in enumerate(hand):
        suit, rank = card.split()
        color = "red" if suit in ['♥️', '♦️'] else "black"
        
        # 卡牌 CSS 樣式
        card_style = f"""
            display: inline-block;
            border: 2px solid #555;
            border-radius: 8px;
            background-color: #f0f2f6;
            color: {color};
            padding: 5px;
            margin: 5px;
            width: 70px;
            height: 100px;
            text-align: center;
            vertical-align: top;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
        """
        content = f"""
            <div style="font-size: 16px; text-align: left; font-weight: bold;">{rank}</div>
            <div style="font-size: 35px; line-height: 50px;">{suit}</div>
        """
        
        # 處理莊家暗牌
        if hidden and index == 1:
            card_style += "background-color: #2b3e50; border: 2px dashed #999;"
            content = """<div style="font-size: 40px; line-height: 90px; color: white;">?</div>"""
            
        cards_html += f'<div style="{card_style}">{content}</div>'
    
    st.markdown(cards_html, unsafe_allow_html=True)

# ==========================================
# 2. 遊戲狀態初始化 (Session State)
# ==========================================

if 'money' not in st.session_state:
    st.session_state.money = 1000  # 初始資金
if 'pot' not in st.session_state:
    st.session_state.pot = 0       # 下注區
if 'current_bet' not in st.session_state:
    st.session_state.current_bet = 0 # 確認後的賭注
if 'deck' not in st.session_state:
    st.session_state.deck = []
if 'player_hand' not in st.session_state:
    st.session_state.player_hand = []
if 'dealer_hand' not in st.session_state:
    st.session_state.dealer_hand = []
if 'game_stage' not in st.session_state:
    st.session_state.game_stage = "BETTING" # 階段: BETTING, PLAYING, INSURANCE, GAMEOVER
if 'message' not in st.session_state:
    st.session_state.message = "請選擇籌碼下注！"

# ==========================================
# 3. 遊戲流程控制
# ==========================================

def add_chip(amount):
    """ 下注 """
    if st.session_state.money >= amount:
        st.session_state.money -= amount
        st.session_state.pot += amount
    else:
        st.toast("餘額不足！")

def clear_bet():
    """ 清除下注 """
    st.session_state.money += st.session_state.pot
    st.session_state.pot = 0

def all_in():
    """ 梭哈 """
    amount = st.session_state.money
    st.session_state.pot += amount
    st.session_state.money = 0

def deal_initial_cards():
    """ 發牌開局 """
    if st.session_state.pot == 0:
        st.toast("請先下注！")
        return

    st.session_state.current_bet = st.session_state.pot
    st.session_state.pot = 0
    
    st.session_state.deck = create_deck()
    st.session_state.player_hand = [st.session_state.deck.pop(), st.session_state.deck.pop()]
    st.session_state.dealer_hand = [st.session_state.deck.pop(), st.session_state.deck.pop()]
    
    # 檢查是否需要買保險 (莊家明牌是 A)
    dealer_up_card_rank = st.session_state.dealer_hand[0].split()[1]
    if dealer_up_card_rank == 'A':
        st.session_state.game_stage = "INSURANCE"
        st.session_state.message = "莊家明牌是 A！要買保險嗎？"
    else:
        check_initial_blackjack()

def buy_insurance(buy):
    """ 保險邏輯 """
    insurance_cost = st.session_state.current_bet / 2
    if buy:
        if st.session_state.money >= insurance_cost:
            st.session_state.money -= insurance_cost
            st.toast(f"已購買保險 (-${insurance_cost})")
        else:
            st.toast("餘額不足買保險，自動跳過")
            buy = False
    
    d_score = calculate_score(st.session_state.dealer_hand)
    if d_score == 21:
        st.session_state.game_stage = "GAMEOVER"
        if buy:
            refund = insurance_cost * 3
            st.session_state.money += refund
            st.session_state.message = "莊家 Blackjack！保險生效，保本！"
        else:
            st.session_state.message = "莊家 Blackjack！你沒買保險，輸了！"
    else:
        if buy:
            st.toast("莊家沒 Blackjack，保險金沒收。")
        check_initial_blackjack()

def check_initial_blackjack():
    """ 檢查玩家起手是否 BJ """
    p_score = calculate_score(st.session_state.player_hand)
    if p_score == 21:
        st.session_state.game_stage = "GAMEOVER"
        win_amount = st.session_state.current_bet * 2.5 # 1.5倍賠率
        st.session_state.money += win_amount
        st.session_state.message = "🎉 Blackjack！贏 1.5 倍！"
    else:
        st.session_state.game_stage = "PLAYING"
        st.session_state.message = "你的回合..."

def hit():
    """ 要牌 (包含特殊牌型檢查) """
    st.session_state.player_hand.append(st.session_state.deck.pop())
    p_score = calculate_score(st.session_state.player_hand)
    p_cards = st.session_state.player_hand
    
    # 1. 檢查 7-7-7 (三張 7 且 21 點 -> 10倍)
    # 判斷方式：手牌數3，每張牌的數字都是 '7'
    is_777 = len(p_cards) == 3 and all(card.split()[1] == '7' for card in p_cards)
    
    if is_777 and p_score == 21:
        st.session_state.game_stage = "GAMEOVER"
        win_amount = st.session_state.current_bet * 11 # 本金 + 10倍
        st.session_state.money += win_amount
        st.session_state.message = "🎰 7-7-7！傳說大獎！贏 10 倍！"
        return

    # 2. 檢查爆牌
    if p_score > 21:
        st.session_state.game_stage = "GAMEOVER"
        st.session_state.message = "💥 爆牌了！"
    
    # 3. 檢查過五關 (5張牌沒爆 -> 5倍)
    elif len(p_cards) == 5:
        st.session_state.game_stage = "GAMEOVER"
        win_amount = st.session_state.current_bet * 6 # 本金 + 5倍
        st.session_state.money += win_amount
        st.session_state.message = "🐲 過五關！超幸運！直接贏 5 倍！"

def double_down():
    """ 加倍下注 """
    extra_bet = st.session_state.current_bet
    if st.session_state.money >= extra_bet:
        st.session_state.money -= extra_bet
        st.session_state.current_bet += extra_bet
        st.toast(f"加倍成功！總賭注: ${st.session_state.current_bet}")
        
        # 加倍只能拿一張牌
        st.session_state.player_hand.append(st.session_state.deck.pop())
        p_score = calculate_score(st.session_state.player_hand)
        
        if p_score > 21:
            st.session_state.game_stage = "GAMEOVER"
            st.session_state.message = "💥 加倍後爆牌了！"
        else:
            # 沒爆牌就強制停牌，進莊家回合
            stand()
    else:
        st.toast("餘額不足，無法加倍！")

def stand():
    """ 停牌 (換莊家行動) """
    # 莊家補牌直到 17 點
    while calculate_score(st.session_state.dealer_hand) < 17:
        st.session_state.dealer_hand.append(st.session_state.deck.pop())
        time.sleep(0.5) # 模擬思考延遲
    
    p_score = calculate_score(st.session_state.player_hand)
    d_score = calculate_score(st.session_state.dealer_hand)
    
    st.session_state.game_stage = "GAMEOVER"
    
    # 結算比大小
    if d_score > 21:
        st.session_state.money += st.session_state.current_bet * 2
        st.session_state.message = "🎉 莊家爆牌！你贏了！"
    elif p_score > d_score:
        st.session_state.money += st.session_state.current_bet * 2
        st.session_state.message = "🎉 你贏了！"
    elif p_score < d_score:
        st.session_state.message = "💸 你輸了..."
    else:
        st.session_state.money += st.session_state.current_bet
        st.session_state.message = "🤝 平手 (退回賭金)"

def reset_game():
    st.session_state.game_stage = "BETTING"
    st.session_state.message = "請下注開始遊戲！"

# ==========================================
# 4. 介面佈局 (UI Layout)
# ==========================================

st.title("🎰 究極 21 點 (6副牌 + 777 + 過五關)")

# 資金顯示
st.metric("💰 你的總資金", f"${st.session_state.money}")

st.divider()

# --- 階段 A: 下注區 ---
if st.session_state.game_stage == "BETTING":
    st.subheader("請選擇籌碼")
    st.info(f"目前下注金額：${st.session_state.pot}")
    
    # 籌碼按鈕 (錢不夠會變灰色 disabled)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.button("$10", on_click=add_chip, args=(10,), disabled=st.session_state.money < 10, use_container_width=True)
    c2.button("$50", on_click=add_chip, args=(50,), disabled=st.session_state.money < 50, use_container_width=True)
    c3.button("$100", on_click=add_chip, args=(100,), disabled=st.session_state.money < 100, use_container_width=True)
    c4.button("$500", on_click=add_chip, args=(500,), disabled=st.session_state.money < 500, use_container_width=True)
    c5.button("All In", on_click=all_in, disabled=st.session_state.money == 0, use_container_width=True)
    
    st.write("")
    col_clear, col_deal = st.columns([1, 2])
    col_clear.button("❌ 清除", on_click=clear_bet, use_container_width=True)
    col_deal.button("🃏 發牌", on_click=deal_initial_cards, type="primary", use_container_width=True)

# --- 階段 B: 遊戲區 ---
else:
    st.caption(f"本局賭注: ${st.session_state.current_bet}")
    
    # 莊家區
    col_d1, col_d2 = st.columns([1, 3])
    with col_d1:
        st.write("### 莊家")
        if st.session_state.game_stage == "GAMEOVER":
            st.write(f"點數: {calculate_score(st.session_state.dealer_hand)}")
        else:
            st.write("點數: ?")
    with col_d2:
        if st.session_state.game_stage == "GAMEOVER":
            display_cards(st.session_state.dealer_hand, hidden=False)
        else:
            display_cards(st.session_state.dealer_hand, hidden=True)

    st.write("---")
    
    # 玩家區
    col_p1, col_p2 = st.columns([1, 3])
    with col_p1:
        st.write("### 你")
        st.write(f"點數: {calculate_score(st.session_state.player_hand)}")
    with col_p2:
        display_cards(st.session_state.player_hand)

    # 訊息通知
    st.info(f"📢 {st.session_state.message}")

    # 操作按鈕區
    if st.session_state.game_stage == "INSURANCE":
        c1, c2 = st.columns(2)
        c1.button("🛡️ 買保險 (賭注的一半)", on_click=buy_insurance, args=(True,), type="primary")
        c2.button("不買", on_click=buy_insurance, args=(False,))
            
    elif st.session_state.game_stage == "PLAYING":
        c1, c2, c3 = st.columns(3)
        c1.button("➕ 加牌 (Hit)", on_click=hit, use_container_width=True)
        c2.button("🛑 停牌 (Stand)", on_click=stand, use_container_width=True)
        
        # 只有手牌 2 張且錢夠時，才能加倍
        if len(st.session_state.player_hand) == 2 and st.session_state.money >= st.session_state.current_bet:
            c3.button("💰 加倍 (Double)", on_click=double_down, type="primary", use_container_width=True)
        else:
            c3.button("💰 加倍", disabled=True, use_container_width=True)
            
    elif st.session_state.game_stage == "GAMEOVER":
        st.button("🔄再來一局", on_click=reset_game, type="primary", use_container_width=True)
