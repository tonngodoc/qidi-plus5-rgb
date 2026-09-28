#!/usr/bin/env bash
# =============================================================================
# QIDI PLUS 5 - RGB EFFECTS MOD UNINSTALLER
# =============================================================================
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=====================================================${NC}"
echo -e "${YELLOW}      GỠ CÀI ĐẶT MOD RGB CHO QIDI PLUS 5            ${NC}"
echo -e "${BLUE}=====================================================${NC}"

NEOPIXEL_PATH="/home/qidi/klipper/klippy/extras/neopixel.py"
BACKUP_PATH="/home/qidi/klipper/klippy/extras/neopixel.py.bak_rgbmod"
MACRO_DIR="/home/qidi/printer_data/config/klipper-macros-qd"
CONFIG_DIR="/home/qidi/printer_data/config"
PRINTER_CFG="$CONFIG_DIR/printer.cfg"

# 1. Restore neopixel.py
if [ -f "$BACKUP_PATH" ]; then
    echo -e "${YELLOW}[*] Đang khôi phục driver neopixel.py gốc...${NC}"
    cp -f "$BACKUP_PATH" "$NEOPIXEL_PATH"
    echo -e "${GREEN}[OK] Đã khôi phục neopixel.py gốc.${NC}"
else
    echo -e "${RED}[WARN] Không tìm thấy bản backup $BACKUP_PATH. Bỏ qua bước khôi phục driver.${NC}"
fi

# 2. Remove macro file
echo -e "${YELLOW}[*] Đang xóa file rgb_effects.cfg...${NC}"
rm -f "$MACRO_DIR/rgb_effects.cfg" "$CONFIG_DIR/rgb_effects.cfg"

# 3. Clean up printer.cfg
if [ -f "$PRINTER_CFG" ]; then
    echo -e "${YELLOW}[*] Dọn dẹp include trong printer.cfg...${NC}"
    sed -i '/rgb_effects.cfg/d' "$PRINTER_CFG"
    sed -i '/# QIDI RGB EFFECTS MOD/d' "$PRINTER_CFG"
    echo -e "${GREEN}[OK] Đã gỡ bỏ cấu hình khỏi printer.cfg.${NC}"
fi

# 4. Restart Klipper
echo -e "${YELLOW}[*] Đang khởi động lại dịch vụ Klipper...${NC}"
if command -v systemctl &> /dev/null; then
    sudo systemctl restart klipper || true
else
    curl -s -X POST http://127.0.0.1:7125/printer/restart || true
fi

echo -e "\n${GREEN}=====================================================${NC}"
echo -e "${GREEN}   ✅ ĐÃ GỠ BỎ MOD THÀNH CÔNG VỀ NGUYÊN BẢN GỐC!    ${NC}"
echo -e "${GREEN}=====================================================${NC}\n"
