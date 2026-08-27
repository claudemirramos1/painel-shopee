cat << 'EOF' > ~/painel-shopee/app.py
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Painel Shopee", layout="wide")

st.title("Painel Shopee")

# Painel flutuante blindado dentro de um componente isolado
components.html("""
<style>
  body { margin: 0; background: transparent; font-family: sans-serif; }
  #widget {
    position: fixed; bottom: 20px; right: 20px; width: 280px;
    background: #f8f9fa; border: 1px solid #ccc; border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2); z-index: 99999;
  }
  #header {
    cursor: move; background: #ee4d2d; color: white; padding: 10px;
    font-weight: bold; border-radius: 7px 7px 0 0; user-select: none;
  }
  #content { padding: 12px; color: #333; }
</style>

<div id="widget">
  <div id="header">Painel Shopee 📱 (Arraste aqui)</div>
  <div id="content">
    <p style="margin:0;">Painel flutuante ativo e funcional!</p>
  </div>
</div>

<script>
  const w = document.getElementById("widget");
  const h = document.getElementById("header");
  let isDragging = false, startX, startY, initX, initY;

  h.addEventListener("mousedown", start);
  h.addEventListener("touchstart", start, {passive: false});
  document.addEventListener("mousemove", move);
  document.addEventListener("touchmove", move, {passive: false});
  document.addEventListener("mouseup", end);
  document.addEventListener("touchend", end);

  function start(e) {
    isDragging = true;
    let cX = e.touches ? e.touches[0].clientX : e.clientX;
    let cY = e.touches ? e.touches[0].clientY : e.clientY;
    let rect = w.getBoundingClientRect();
    startX = cX; startY = cY;
    initX = rect.left; initY = rect.top;
    w.style.bottom = "auto"; w.style.right = "auto";
    w.style.left = initX + "px"; w.style.top = initY + "px";
    e.preventDefault();
  }

  function move(e) {
    if (!isDragging) return;
    let cX = e.touches ? e.touches[0].clientX : e.clientX;
    let cY = e.touches ? e.touches[0].clientY : e.clientY;
    w.style.left = (initX + (cX - startX)) + "px";
    w.style.top = (initY + (cY - startY)) + "px";
    e.preventDefault();
  }

  function end() { isDragging = false; }
</script>
""", height=220)
EOF
