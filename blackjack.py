import streamlit as st
import random

# --- 1. 核心邏輯區 (函式) ---

def create_deck():
    """ 建立一副 52 張的撲克牌，使用 Emoji """
    suits = ['♠️', '♥️', '♦️', '♣️']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    deck = []
    for suit in suits:
        for rank in ranks:
            deck.append(f"{suit} {rank}")
    random.shuffle(deck)
    return deck

def calculate_score(hand):
    """ 計算手牌分數，處理 A 的 1 或 11 點邏輯 """
    score = 0
    aces = 0
    
    for card in hand:
        rank = card.split()[1] # 取得花色後面的數字/文字
        if rank in ['J', 'Q', 'K']:
            score += 10
        elif rank == 'A':
            aces += 1
            score += 11
        else:
            score += int(rank)
            
    # 如果爆牌了 (超過 21) 且還有 A，把 A 當作 1 點
    while score > 21 and aces > 0:
        score -= 10
        aces -= 1
        
    return score

# --- 2. 遊戲初始化 (Session State) ---
# Streamlit 每次按按鈕都會重跑程式，所以要把變數存在 session_state 裡

if 'deck' not in st.session_state:
    st.session_state.deck = []
if 'player_hand' not in st.session_state:
    st.session_state.player_hand = []
if 'dealer_hand' not in st.session_state:
    st.session_state.dealer_hand = []
if 'game_over' not in st.session_state:
    st.session_state.game_over = True # 一開始設為 True 讓玩家按「開始遊戲」
if 'message' not in st.session_state:
    st.session_state.message = "點擊下方按鈕開始遊戲！"

# --- 3. 按鈕事件處理 ---

def start_game():
    st.session_state.deck = create_deck()
    st.session_state.player_hand = [st.session_state.deck.pop(), st.session_state.deck.pop()]
    st.session_state.dealer_hand = [st.session_state.deck.pop(), st.session_state.deck.pop()]
    st.session_state.game_over = False
    st.session_state.message = "你的回合：要加牌 (Hit) 還是停牌 (Stand)？"

def hit():
    card = st.session_state.deck.pop()
    st.session_state.player_hand.append(card)
    p_score = calculate_score(st.session_state.player_hand)
    
    if p_score > 21:
        st.session_state.message = "💥 爆牌了！你輸了！"
        st.session_state.game_over = True

def stand():
    # 玩家停牌，換莊家行動
    p_score = calculate_score(st.session_state.player_hand)
    d_score = calculate_score(st.session_state.dealer_hand)
    
    # 莊家邏輯：小於 17 點必須加牌
    while d_score < 17:
        st.session_state.dealer_hand.append(st.session_state.deck.pop())
        d_score = calculate_score(st.session_state.dealer_hand)
    
    # 結算勝負
    if d_score > 21:
        st.session_state.message = "🎉 莊家爆牌！你贏了！"
    elif p_score > d_score:
        st.session_state.message = "🎉 你的點數比較大！你贏了！"
    elif p_score < d_score:
        st.session_state.message = "💸 莊家點數比較大，你輸了..."
    else:
        st.session_state.message = "🤝 平手 (Push)！"
    
    st.session_state.game_over = True

# --- 4. 畫面顯示 (UI) ---

st.title("🎲 Streamlit 21 點 (無圖檔版)")
st.write(st.session_state.message)

# 顯示遊戲區域 (如果遊戲正在進行或剛結束)
if st.session_state.deck:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("你的手牌")
        # 顯示卡牌
        st.info("  ".join(st.session_state.player_hand)) 
        p_score = calculate_score(st.session_state.player_hand)
        st.write(f"目前點數：**{p_score}**")

    with col2:
        st.subheader("莊家的手牌")
        if st.session_state.game_over:
            # 遊戲結束，翻開所有牌
            st.warning("  ".join(st.session_state.dealer_hand))
            d_score = calculate_score(st.session_state.dealer_hand)
            st.write(f"莊家點數：**{d_score}**")
        else:
            # 遊戲中，蓋住一張牌
            hidden_card = "🂠 (蓋牌)" # 也可以用 ? 代替
            visible_card = st.session_state.dealer_hand[0]
            st.warning(f"{visible_card}   {hidden_card}")
            st.write("莊家點數：?")

# 操作按鈕
st.write("---")
if st.session_state.game_over:
    st.button("🔄 開始新的一局", on_click=start_game, type="primary")
else:
    col_a, col_b = st.columns(2)
    with col_a:
        st.button("➕ 加牌 (Hit)", on_click=hit, use_container_width=True)
    with col_b:
        st.button("🛑 停牌 (Stand)", on_click=stand, use_container_width=True)
