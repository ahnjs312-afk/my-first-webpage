import streamlit as st
import random

st.title("⭕❌ 틱택토: vs 컴퓨터")

if "board" not in st.session_state:
    st.session_state.board = [""] * 9
    st.session_state.winner = None

def check_winner(board):
    lines = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a,b,c in lines:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    if "" not in board:
        return "draw"
    return None

def player_move(i):
    if st.session_state.board[i] == "" and not st.session_state.winner:
        st.session_state.board[i] = "❌"
        st.session_state.winner = check_winner(st.session_state.board)
        if not st.session_state.winner:
            empty = [j for j,v in enumerate(st.session_state.board) if v == ""]
            if empty:
                st.session_state.board[random.choice(empty)] = "⭕"
                st.session_state.winner = check_winner(st.session_state.board)

for row in range(3):
    cols = st.columns(3)
    for col in range(3):
        i = row * 3 + col
        cols[col].button(
            st.session_state.board[i] or " ",
            key=f"cell{i}",
            on_click=player_move, args=(i,)
        )

if st.session_state.winner == "❌":
    st.success("🎉 당신이 이겼어요!")
elif st.session_state.winner == "⭕":
    st.error("컴퓨터가 이겼어요 😢")
elif st.session_state.winner == "draw":
    st.info("무승부예요!")

if st.button("다시 시작"):
    st.session_state.board = [""] * 9
    st.session_state.winner = None
    st.rerun()
