import streamlit as st
import random

# --- 1. 核心邏輯區 (無需更動) ---

def create_deck():
    suits = ['♠️', '♥️', '♦️', '♣️']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    deck = [f"{suit} {rank}" for suit in suits for rank in ranks]
    random.shuffle(deck)
    return deck

def calculate_score(hand):
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
    while score > 21 and aces > 0:
        score -= 10
        aces -= 1
    return score

# --- 2. 新增：畫卡牌的魔法函式 (CSS) ---
# 這裡就是用程式碼「畫線」做成卡片的關鍵

def display_cards(hand, hidden=False):
    """
    將手牌轉換成漂亮的 HTML 卡片顯示
    hand: 手牌列表
    hidden: 是否隱藏第一張牌 (莊家專用)
    """
    cards_html = ""
    for index, card in enumerate(hand):
        # 預設樣式
        suit, rank = card.split()
        color = "red" if suit in ['♥️', '♦️'] else "black"
        
        # 卡片的外框樣式 (CSS)
        card_style = f"""
            display: inline-block;
            border: 2px solid #555;      /* 這就是你要的線！ */
            border-radius: 8px;          /* 圓角 */
            background-color: #f0f2f6;   /* 卡片底色 (淺灰) */
            color: {color};              /* 字體顏色 */
            padding: 5px;
            margin: 5px;
            width: 70px;
            height: 100px;
            text-align: center;
            vertical-align: top;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2); /* 陰影 */
        """
        
        # 內容樣式
        content = f"""
            <div style="font-size: 16px; text-align: left; font-weight: bold;">{rank}</div>
            <div style="font-size: 35px; line-height: 50px;">{suit}</div>
        """
        
        # 如果是莊家的暗牌 (只隱藏第二張以後的牌? 不，通常隱藏第二張)
        # 這裡邏輯調整：如果是莊家且 hidden=True，第一張顯示，第二張蓋住
        if hidden and index == 1:
            card_style += "background-color: #2b3e50; border: 2px dashed #999;"
            content = """
            <div style="font-size: 40px; line-height: 90px; color: white;">?</div>
            """
            
        cards_html += f'<div style="{card_style}">{content}</div>'
    
    # 使用 st.markdown 渲染 HTML
    st.markdown(cards_html, unsafe_allow_html=True)


# --- 3. 狀態初始化 ---

if 'money' not in st.session_state:
    st.session_state.money = 1000
if 'current_bet' not in st.session_state:
    st.session_state.current_bet = 0
if 'deck' not in st.session_state:
    st.session_state.deck = []
if 'player_hand' not in st.session_state:
    st.session_state.player_hand = []
if 'dealer_hand' not in st.session_state:
    st.session_state.dealer_hand = []
if 'game_stage' not in st.session_state:
    st.session_state.game_stage = "BETTING"
if 'message' not in st.session_state:
    st.session_state.message = "請下注開始遊戲！"

# --- 4. 遊戲流程函式 ---

def deal_initial_cards():
    bet_amount = 100
    if st.session_state.money < bet_amount:
        st.session_state.message = "💸 破產了！請重新整理頁面重置。"
        return

    st.session_state.current_bet = bet_amount
    st.session_state.money -= bet_amount
    
    st.session_state.deck = create_deck()
    st.session_state.player_hand = [st.session_state.deck.pop(), st.session_state.deck.pop()]
    st.session_state.dealer_hand = [st.session_state.deck.pop(), st.session_state.deck.pop()]
    
    # 檢查保險
    dealer_up_card_rank = st.session_state.dealer_hand[0].split()[1]
    if dealer_up_card_rank == 'A':
        st.session_state.game_stage = "INSURANCE"
        st.session_state.message = "莊家明牌是 A！要買保險嗎？"
    else:
        check_initial_blackjack()

def buy_insurance(buy):
    insurance_cost = st.session_state.current_bet / 2
    if buy:
        st.session_state.money -= insurance_cost
        st.toast(f"💸 已購買保險 (-${insurance_cost})")
    
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
    p_score = calculate_score(st.session_state.player_hand)
    if p_score == 21:
        st.session_state.game_stage = "GAMEOVER"
        win_amount = st.session_state.current_bet * 2.5
        st.session_state.money += win_amount
        st.session_state.message = "🎉 Blackjack！贏 1.5 倍！"
    else:
        st.session_state.game_stage = "PLAYING"
        st.session_state.message = "你的回合..."

def hit():
    st.session_state.player_hand.append(st.session_state.deck.pop())
    if calculate_score(st.session_state.player_hand) > 21:
        st.session_state.game_stage = "GAMEOVER"
        st.session_state.message = "💥 爆牌了！"

def stand():
    while calculate_score(st.session_state.dealer_hand) < 17:
        st.session_state.dealer_hand.append(st.session_state.deck.pop())
        time.sleep(0.5) # 稍微停頓增加緊張感 (需 import time)
    
    p_score = calculate_score(st.session_state.player_hand)
    d_score = calculate_score(st.session_state.dealer_hand)
    
    st.session_state.game_stage = "GAMEOVER"
    
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

# --- 5. 介面顯示 (UI) ---

st.title("🃏 21 點 (CSS 卡牌版)")
st.metric("💰 資金池", f"${st.session_state.money}")
st.info(f"📢 {st.session_state.message}")

if st.session_state.game_stage == "BETTING":
    st.button("下注 $100 發牌", on_click=deal_initial_cards, type="primary", use_container_width=True)

else:
    # 莊家區
    st.caption("莊家的手牌")
    if st.session_state.game_stage == "GAMEOVER":
        display_cards(st.session_state.dealer_hand, hidden=False)
        st.write(f"莊家點數：**{calculate_score(st.session_state.dealer_hand)}**")
    else:
        display_cards(st.session_state.dealer_hand, hidden=True)
        st.write("莊家點數：?")

    st.divider()

    # 玩家區
    st.caption("你的手牌")
    display_cards(st.session_state.player_hand)
    st.write(f"目前點數：**{calculate_score(st.session_state.player_hand)}**")

    st.write("---")

    # 按鈕區
    if st.session_state.game_stage == "INSURANCE":
        c1, c2 = st.columns(2)
        c1.button("🛡️ 買保險 ($50)", on_click=buy_insurance, args=(True,), type="primary")
        c2.button("不買", on_click=buy_insurance, args=(False,))
            
    elif st.session_state.game_stage == "PLAYING":
        c1, c2 = st.columns(2)
        c1.button("➕ 加牌", on_click=hit, use_container_width=True)
        c2.button("🛑 停牌", on_click=stand, use_container_width=True)
            
    elif st.session_state.game_stage == "GAMEOVER":
        st.button("🔄再來一局", on_click=reset_game, type="primary", use_container_width=True)

# 補上漏掉的 import
import time
