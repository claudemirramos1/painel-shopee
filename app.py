import streamlit as st

st.set_page_config(page_title="Painel Shopee", layout="wide")

st.title("Painel Shopee")

# Widget flutuante injetado via HTML/CSS/JS direto
st.markdown("""
<div id="painel-flutuante" style="position: fixed; bottom: 20px; right: 20px; z-index: 999999; width: 300px; background: #f8f9fa; border: 1px solid #ccc; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
    <div id="painel-header" style="cursor: move; padding: 10px; background-color: #ee4d2d; color: white; border-radius: 7px 7px 0 0; font-weight: bold; user-select: none;">
        Painel Flutuante 📱
    </div>
    <div style="padding: 12px;">
        <p style="margin: 0; color: #333;">Arraste pelo cabeçalho para mover.</p>
    </div>
</div>

<script>
const box = document.getElementById("painel-flutuante");
const header = document.getElementById("painel-header");

let isDragging = false, startX, startY, initialLeft, initialTop;

header.addEventListener("mousedown", dragStart);
header.addEventListener("touchstart", dragStart, {passive: false});

document.addEventListener("mousemove", drag);
document.addEventListener("touchmove", drag, {passive: false});

document.addEventListener("mouseup", dragEnd);
document.addEventListener("touchend", dragEnd);

function dragStart(e) {
    isDragging = true;
    let clientX = e.type === "touchstart" ? e.touches[0].clientX : e.clientX;
    let clientY = e.type === "touchstart" ? e.touches[0].clientY : e.clientY;
    
    let rect = box.getBoundingClientRect();
    startX = clientX;
    startY = clientY;
    initialLeft = rect.left;
    initialTop = rect.top;
    
    box.style.bottom = "auto";
    box.style.right = "auto";
    box.style.left = initialLeft + "px";
    box.style.top = initialTop + "px";
    e.preventDefault();
}

function drag(e) {
    if (!isDragging) return;
    let clientX = e.type === "touchmove" ? e.touches[0].clientX : e.clientX;
    let clientY = e.type === "touchmove" ? e.touches[0].clientY : e.clientY;
    
    box.style.left = (initialLeft + (clientX - startX)) + "px";
    box.style.top = (initialTop + (clientY - startY)) + "px";
    e.preventDefault();
}

function dragEnd() {
    isDragging = false;
}
</script>
""", unsafe_allow_html=True)
