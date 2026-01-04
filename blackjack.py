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
