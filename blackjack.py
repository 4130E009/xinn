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
    deck = [f"{suit} {rank}" for suit in suits for rank in ranks] * 6
    random.shuffle(deck)
    return deck

def get_card_value(card):
    rank = card.split()[1]
    if rank in ['J', 'Q', 'K']:
        return 10
    elif rank == 'A':
        return 11
    else:
        return int(rank)

def calculate_score(hand):
    score = 0
    aces = 0
    for card in hand:
        val = get_card_value(card)
        score += val
        if val == 11:
            aces += 1
    
    while score > 21 and aces > 0:
        score -= 10
        aces -= 1
    return score

def display_cards(hand, hidden=False, active=False):
    """ 繪製卡牌 """
    cards_html = ""
    container_style = ""
    if active:
        container_style = "border: 3px solid #FFD700; border-radius: 10px; padding: 10px; background-color: rgba(255, 215, 0, 0.1);"
    
    for index, card in enumerate(hand):
        suit, rank = card.split()
        color = "red" if suit in ['♥️', '♦️'] else "black"
        
        card_style = f"""
            display: inline-block;
            border: 2px solid #555;
            border-radius: 8px;
            background-color: #f0f2f6;
            color: {color};
            padding: 5px;
            margin: 5px;
            width: 60px;
            height: 90px;
            text-align: center;
            vertical-align: top;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
        """
        content = f"""
            <div style="font-size: 14px; text-align: left; font-weight: bold;">{rank}</div>
            <div style="font-size: 30px; line-height: 45px;">{suit}</div>
        """
        
        if hidden and index == 1:
            card_style += "background-color: #2b3e50; border: 2px dashed #999;"
            content = """<div style="font-size: 35px; line-height: 80px; color: white;">?</div>"""
            
        cards_html += f'<div style="{card_style}">{content}</div>'
    
    st.markdown(f'<div style="{container_style}">{cards_html}</div>', unsafe_allow_html=True)

# ==========================================
# 2. 遊戲狀態初始化
# ==========================================

# 修改點 1：初始資金改為 5000
if 'money' not in st.session_state:
    st.session_state.money = 5000

if 'pot' not in st.session_state:
    st.session_state.pot = 0
if 'deck' not in st.session_state:
    st.session_state.deck = []
if 'dealer_hand' not in st.session_state:
    st.session_state.dealer_hand = []

# 多手牌變數
if 'player_hands' not in st.session_state:
    st.session_state.player_hands = [] 
if 'current_bets' not in st.session_state:
    st.session_state.current_bets = []
if 'hand_status' not in st.session_state:
    st.session_state.hand_status = []
if 'active_hand_idx' not in st.session_state:
    st.session_state.active_hand_idx = 0

if 'game_stage' not in st.session_state:
    st.session_state.game_stage = "BETTING"
if 'message' not in st.session_state:
    st.session_state.message = "請選擇籌碼下注！"

# ==========================================
# 3. 遊戲流程控制
# ==========================================

def add_chip(amount):
    if st.session_state.money >= amount:
        st.session_state.money -= amount
        st.session_state.pot += amount
    else:
        st.toast("餘額不足！")

def clear_bet():
    st.session_state.money += st.session_state.pot
    st.session_state.pot = 0

def all_in():
    amount = st.session_state.money
    st.session_state.pot += amount
    st.session_state.money = 0

# 修改點 2：每日補給機制
def daily_refill():
    st.session_state.money = 5000
    st.session_state.pot = 0
    st.toast("🌙 時間來到隔日 00:00，資金已補回 $5000！")

def deal_initial_cards():
    if st.session_state.pot == 0:
        st.toast("請先下注！")
        return

    # 初始化
    st.session_state.current_bets = [st.session_state.pot]
    st.session_state.pot = 0
    st.session_state.deck = create_deck()
    
    # 發牌
    p_hand = [st.session_state.deck.pop(), st.session_state.deck.pop()]
    st.session_state.player_hands = [p_hand]
    st.session_state.hand_status = ["PLAYING"]
    st.session_state.active_hand_idx = 0
    st.session_state.dealer_hand = [st.session_state.deck.pop(), st.session_state.deck.pop()]
    
    # 檢查保險
    dealer_up = st.session_state.dealer_hand[0].split()[1]
    if dealer_up == 'A':
        st.session_state.game_stage = "INSURANCE"
        st.session_state.message = "莊家明牌是 A！要買保險嗎？"
    else:
        check_initial_blackjack()

def buy_insurance(buy):
    cost = st.session_state.current_bets[0] / 2
    if buy:
        if st.session_state.money >= cost:
            st.session_state.money -= cost
            st.toast(f"已購買保險 (-${cost})")
        else:
            st.toast("餘額不足，跳過保險")
            buy = False
    
    d_score = calculate_score(st.session_state.dealer_hand)
    if d_score == 21:
        st.session_state.game_stage = "GAMEOVER"
        if buy:
            st.session_state.money += cost * 3
            st.session_state.message = "莊家 Blackjack！保險生效保本！"
        else:
            st.session_state.message = "莊家 Blackjack！你輸了！"
    else:
        if buy: st.toast("保險金沒收")
        check_initial_blackjack()

def check_initial_blackjack():
    p_score = calculate_score(st.session_state.player_hands[0])
    if p_score == 21:
        st.session_state.hand_status[0] = "BJ"
        next_hand_or_end()
    else:
        st.session_state.game_stage = "PLAYING"
        st.session_state.message = "你的回合..."

def split_hand():
    idx = st.session_state.active_hand_idx
    bet = st.session_state.current_bets[idx]
    if st.session_state.money < bet:
        st.toast("餘額不足，無法分牌！")
        return
    
    st.session_state.money -= bet
    current_hand = st.session_state.player_hands[idx]
    
    new_hand1 = [current_hand[0], st.session_state.deck.pop()]
    new_hand2 = [current_hand[1], st.session_state.deck.pop()]
    
    st.session_state.player_hands = [new_hand1, new_hand2]
    st.session_state.current_bets = [bet, bet]
    st.session_state.hand_status = ["PLAYING", "PLAYING"]
    st.session_state.active_hand_idx = 0
    
    st.toast("✂️ 分牌成功！")
    
    if calculate_score(new_hand1) == 21:
        st.session_state.hand_status[0] = "STAND"
        next_hand_or_end()

def hit():
    idx = st.session_state.active_hand_idx
    st.session_state.player_hands[idx].append(st.session_state.deck.pop())
    
    hand = st.session_state.player_hands[idx]
    score = calculate_score(hand)
    
    is_777 = len(hand) == 3 and all(c.split()[1] == '7' for c in hand)
    if is_777 and score == 21:
        st.session_state.hand_status[idx] = "777"
        st.toast(f"手牌 {idx+1}: 7-7-7 大獎！")
        next_hand_or_end()
        return

    if score > 21:
        st.session_state.hand_status[idx] = "BUST"
        st.toast(f"手牌 {idx+1}: 爆牌！")
        next_hand_or_end()
    elif len(hand) == 5:
        st.session_state.hand_status[idx] = "5-DRAGON"
        st.toast(f"手牌 {idx+1}: 過五關！")
        next_hand_or_end()

def double_down():
    idx = st.session_state.active_hand_idx
    bet = st.session_state.current_bets[idx]
    
    if st.session_state.money >= bet:
        st.session_state.money -= bet
        st.session_state.current_bets[idx] += bet
        st.session_state.player_hands[idx].append(st.session_state.deck.pop())
        score = calculate_score(st.session_state.player_hands[idx])
        
        if score > 21:
            st.session_state.hand_status[idx] = "BUST"
        else:
            st.session_state.hand_status[idx] = "STAND"
        next_hand_or_end()
    else:
        st.toast("餘額不足！")

def stand():
    idx = st.session_state.active_hand_idx
    st.session_state.hand_status[idx] = "STAND"
    next_hand_or_end()

def next_hand_or_end():
    if st.session_state.active_hand_idx < len(st.session_state.player_hands) - 1:
        st.session_state.active_hand_idx += 1
    else:
        run_dealer_turn()

def run_dealer_turn():
    st.session_state.game_stage = "GAMEOVER"
    all_bust = all(s in ['BUST'] for s in st.session_state.hand_status)
    if all_bust:
        st.session_state.message = "😭 全部爆牌，莊家躺贏..."
        return

    while calculate_score(st.session_state.dealer_hand) < 17:
        st.session_state.dealer_hand.append(st.session_state.deck.pop())
        time.sleep(0.5)
    
    d_score = calculate_score(st.session_state.dealer_hand)
    msg_list = []
    
    for i, hand in enumerate(st.session_state.player_hands):
        status = st.session_state.hand_status[i]
        bet = st.session_state.current_bets[i]
        p_score = calculate_score(hand)
        hand_name = f"手牌 {i+1}"
        
        if status == "BUST":
            msg_list.append(f"{hand_name}: 💥 爆牌輸掉")
        elif status == "BJ":
            st.session_state.money += bet * 2.5
            msg_list.append(f"{hand_name}: 🎉 Blackjack (1.5倍)!")
        elif status == "5-DRAGON":
            st.session_state.money += bet * 6
            msg_list.append(f"{hand_name}: 🐲 過五關 (5倍)!")
        elif status == "777":
            st.session_state.money += bet * 11
            msg_list.append(f"{hand_name}: 🎰 7-7-7 (10倍)!")
        else: # STAND
            if d_score > 21:
                st.session_state.money += bet * 2
                msg_list.append(f"{hand_name}: 🎉 贏了 (莊家爆)!")
            elif p_score > d_score:
                st.session_state.money += bet * 2
                msg_list.append(f"{hand_name}: 🎉 贏了!")
            elif p_score < d_score:
                msg_list.append(f"{hand_name}: 💸 輸了...")
            else:
                st.session_state.money += bet
                msg_list.append(f"{hand_name}: 🤝 平手")

    st.session_state.message = " | ".join(msg_list)

def reset_game():
    st.session_state.game_stage = "BETTING"
    st.session_state.message = "請下注開始遊戲！"

# ==========================================
# 4. 介面佈局
# ==========================================

st.title("🎰 21 點豪華版 (含隔日補幣)")
st.metric("💰 資金", f"${st.session_state.money}")
st.divider()

# --- 介面修改：補幣機制 ---
# 只有在「下注階段」且「錢低於2000」且「還沒下注」時，顯示補幣選項

if st.session_state.game_stage == "BETTING":
    
    # 補幣按鈕區塊
    if st.session_state.money < 2000 and st.session_state.pot == 0:
        st.warning("⚠️ 資金低於 $2000！觸發補貼機制：")
        st.button("🌙 模擬時間快轉到隔日 00:00 (補滿 $5000)", on_click=daily_refill, type="primary", use_container_width=True)
        st.write("---")

    # 下注區
    st.info(f"下注額: ${st.session_state.pot}")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.button("$10", on_click=add_chip, args=(10,), disabled=st.session_state.money<10, use_container_width=True)
    c2.button("$50", on_click=add_chip, args=(50,), disabled=st.session_state.money<50, use_container_width=True)
    c3.button("$100", on_click=add_chip, args=(100,), disabled=st.session_state.money<100, use_container_width=True)
    c4.button("$500", on_click=add_chip, args=(500,), disabled=st.session_state.money<500, use_container_width=True)
    c5.button("All In", on_click=all_in, disabled=st.session_state.money==0, use_container_width=True)
    
    st.write("")
    col_x, col_go = st.columns([1,2])
    col_x.button("❌ 清除", on_click=clear_bet, use_container_width=True)
    col_go.button("🃏 發牌", on_click=deal_initial_cards, type="primary", use_container_width=True)

else:
    # 莊家與玩家區 (維持不變)
    col_d1, col_d2 = st.columns([1, 4])
    with col_d1:
        st.write("#### 莊家")
        if st.session_state.game_stage == "GAMEOVER":
            st.write(f"點數: {calculate_score(st.session_state.dealer_hand)}")
        else:
            st.write("點數: ?")
    with col_d2:
        if st.session_state.game_stage == "GAMEOVER":
            display_cards(st.session_state.dealer_hand, hidden=False)
        else:
            display_cards(st.session_state.dealer_hand, hidden=True)
    
    st.divider()
    
    st.write("#### 你的手牌")
    cols = st.columns(len(st.session_state.player_hands))
    for i, hand in enumerate(st.session_state.player_hands):
        with cols[i]:
            score = calculate_score(hand)
            bet = st.session_state.current_bets[i]
            status = st.session_state.hand_status[i]
            is_active = (i == st.session_state.active_hand_idx) and (st.session_state.game_stage == "PLAYING")
            title_text = f"手牌 {i+1} (${bet})"
            if is_active: title_text = f"🔴 {title_text}"
            st.caption(title_text)
            display_cards(hand, active=is_active)
            st.write(f"點數: **{score}** ({status})")

    st.info(f"📢 {st.session_state.message}")

    if st.session_state.game_stage == "INSURANCE":
        c1, c2 = st.columns(2)
        c1.button("🛡️ 買保險", on_click=buy_insurance, args=(True,), type="primary")
        c2.button("不買", on_click=buy_insurance, args=(False,))
        
    elif st.session_state.game_stage == "PLAYING":
        active_idx = st.session_state.active_hand_idx
        active_hand = st.session_state.player_hands[active_idx]
        active_bet = st.session_state.current_bets[active_idx]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.button("➕ 加牌", on_click=hit, use_container_width=True)
        c2.button("🛑 停牌", on_click=stand, use_container_width=True)
        
        can_double = len(active_hand) == 2 and st.session_state.money >= active_bet
        c3.button("💰 加倍", on_click=double_down, disabled=not can_double, use_container_width=True)
        
        can_split = (len(active_hand) == 2 and 
                     get_card_value(active_hand[0]) == get_card_value(active_hand[1]) and 
                     len(st.session_state.player_hands) == 1 and
                     st.session_state.money >= active_bet)
        c4.button("✂️ 分牌", on_click=split_hand, disabled=not can_split, use_container_width=True)
        
    elif st.session_state.game_stage == "GAMEOVER":
        st.button("🔄 再來一局", on_click=reset_game, type="primary", use_container_width=True)
