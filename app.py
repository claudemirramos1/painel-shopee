import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Painel Shopee", layout="wide")

st.title("Painel Shopee")

html_code = """
<div id="floating-widget-container">
    <div id="floating-widget-header" style="cursor: move; padding: 10px; background-color: #ee4d2d; color: white; border-radius: 8px 8px 0 0; font-weight: bold; user-select: none;">
        Painel Flutuante
    </div>
    <div id="floating-widget-body" style="padding: 10px; background-color: #f8f9fa; border: 1px solid #ccc; border-radius: 0 0 8px 8px;">
        <p>Conteúdo do Widget Flutuante Shopee</p>
    </div>
</div>

<script>
    function initFloatingWidget() {
        let parentDoc = window.parent.document;
        let box = parentDoc.querySelector('div[data-testid="stCustomComponentV1"]');
        if (!box) return;

        let header = box.querySelector("#floating-widget-header") || box;

        let isDragging = false;
        let isPinching = false;
        let startX, startY, initialLeft, initialTop;
        let initialPinchDist = 0;
        let initialPinchWidth = 0;

        header.addEventListener("mousedown", dragStart);
        parentDoc.addEventListener("mousemove", drag);
        parentDoc.addEventListener("mouseup", dragEnd);

        header.addEventListener("touchstart", dragStart, { passive: false });
        parentDoc.addEventListener("touchmove", drag, { passive: false });
        parentDoc.addEventListener("touchend", dragEnd);

        function getDistance(t1, t2) {
            return Math.hypot(t1.clientX - t2.clientX, t1.clientY - t2.clientY);
        }

        header.addEventListener("touchstart", function(e) {
            if (e.touches.length === 2) {
                isPinching = true;
                initialPinchDist = getDistance(e.touches[0], e.touches[1]);
                initialPinchWidth = box.offsetWidth;
                e.preventDefault();
            }
        }, { passive: false });

        parentDoc.addEventListener("touchmove", function(e) {
            if (isPinching && e.touches.length === 2) {
                let currentDist = getDistance(e.touches[0], e.touches[1]);
                let factor = currentDist / initialPinchDist;
                let newWidth = Math.min(Math.max(initialPinchWidth * factor, 180), parentDoc.documentElement.clientWidth - 20);
                box.style.width = newWidth + "px";
                e.preventDefault();
            }
        }, { passive: false });

        parentDoc.addEventListener("touchend", function(e) {
            if (e.touches.length < 2) {
                isPinching = false;
            }
        });

        function dragStart(e) {
            if (isPinching) return;
            let clientX = e.type === "touchstart" ? e.touches[0].clientX : e.clientX;
            let clientY = e.type === "touchstart" ? e.touches[0].clientY : e.clientY;
            
            let rect = box.getBoundingClientRect();
            let parentRect = parentDoc.documentElement.getBoundingClientRect();

            isDragging = true;
            startX = clientX;
            startY = clientY;
            initialLeft = rect.left - parentRect.left;
            initialTop = rect.top - parentRect.top;
            
            box.style.bottom = "auto";
            box.style.right = "auto";
            box.style.left = initialLeft + "px";
            box.style.top = initialTop + "px";
        }

        function drag(e) {
            if (!isDragging || isPinching) return;
            let clientX = e.type === "touchmove" ? e.touches[0].clientX : e.clientX;
            let clientY = e.type === "touchmove" ? e.touches[0].clientY : e.clientY;

            let dx = clientX - startX;
            let dy = clientY - startY;

            let newLeft = initialLeft + dx;
            let newTop = initialTop + dy;

            let maxLeft = parentDoc.documentElement.clientWidth - box.offsetWidth;
            let maxTop = parentDoc.documentElement.clientHeight - box.offsetHeight;

            newLeft = Math.max(0, Math.min(newLeft, maxLeft));
            newTop = Math.max(0, Math.min(newTop, maxTop));

            box.style.left = newLeft + "px";
            box.style.top = newTop + "px";
            
            if (e.type === "touchmove") {
                e.preventDefault();
            }
        }

        function dragEnd() {
            isDragging = false;
        }
    }

    let checkExist = setInterval(function() {
        let parentDoc = window.parent.document;
        let targetDiv = parentDoc.querySelector('div[data-testid="stCustomComponentV1"]');
        if (targetDiv) {
            targetDiv.style.position = "fixed";
            targetDiv.style.zIndex = "999999";
            targetDiv.style.bottom = "20px";
            targetDiv.style.right = "20px";
            targetDiv.style.width = "auto";
            targetDiv.style.height = "auto";
            
            initFloatingWidget();
            clearInterval(checkExist);
        }
    }, 200);
</script>
"""

components.html(html_code, height=0)
