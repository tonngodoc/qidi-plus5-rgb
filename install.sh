#!/usr/bin/env bash
# =============================================================================
# QIDI PLUS 5 - RGB EFFECTS MOD INSTALLER
# Repo: https://github.com/tonngodoc/qidi-plus5-rgb
# =============================================================================
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================================${NC}"
echo -e "${GREEN}      QIDI PLUS 5 - RGB EFFECTS MOD INSTALLER       ${NC}"
echo -e "${BLUE}=====================================================${NC}"

KLIPPER_DIR="/home/qidi/klipper"
CONFIG_DIR="/home/qidi/printer_data/config"
MACRO_DIR="/home/qidi/printer_data/config/klipper-macros-qd"
INSTALL_DIR="/home/qidi/qidi-plus5-rgb"

# 1. Check Klipper environment
if [ ! -d "$KLIPPER_DIR" ]; then
    echo -e "${RED}[ERROR] Không tìm thấy thư mục Klipper tại $KLIPPER_DIR!${NC}"
    echo "Script này chỉ dành cho máy in Qidi chạy Klipper."
    exit 1
fi

# 2. Resolve script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
if [ ! -f "$SCRIPT_DIR/patch_neopixel.py" ]; then
    echo -e "${YELLOW}[*] Đang tải mã nguồn mod về $INSTALL_DIR...${NC}"
    if [ -d "$INSTALL_DIR" ]; then
        cd "$INSTALL_DIR" && git pull || true
    else
        git clone https://github.com/tonngodoc/qidi-plus5-rgb.git "$INSTALL_DIR"
    fi
    SCRIPT_DIR="$INSTALL_DIR"
fi

cd "$SCRIPT_DIR"

# 3. Patch neopixel driver in Klipper
echo -e "${YELLOW}[*] Đang vá driver NeoPixel (Klipper reactor animation)...${NC}"
python3 "$SCRIPT_DIR/patch_neopixel.py"

# 4. Copy macro configuration file
echo -e "${YELLOW}[*] Đang cấu hình macro Klipper...${NC}"
if [ -d "$MACRO_DIR" ]; then
    TARGET_CFG="$MACRO_DIR/rgb_effects.cfg"
    INCLUDE_LINE="[include klipper-macros-qd/rgb_effects.cfg]"
else
    TARGET_CFG="$CONFIG_DIR/rgb_effects.cfg"
    INCLUDE_LINE="[include rgb_effects.cfg]"
fi

cp -f "$SCRIPT_DIR/rgb_effects.cfg" "$TARGET_CFG"
echo -e "${GREEN}[OK] Đã sao chép: $TARGET_CFG${NC}"

# 5. Add include to printer.cfg if missing
PRINTER_CFG="$CONFIG_DIR/printer.cfg"
if [ -f "$PRINTER_CFG" ]; then
    if ! grep -q "rgb_effects.cfg" "$PRINTER_CFG"; then
        echo -e "${YELLOW}[*] Thêm $INCLUDE_LINE vào printer.cfg...${NC}"
        echo -e "\n# QIDI RGB EFFECTS MOD\n$INCLUDE_LINE" >> "$PRINTER_CFG"
    else
        echo -e "${GREEN}[OK] printer.cfg đã chứa khai báo rgb_effects.cfg.${NC}"
    fi
fi

# 6. Configure Fluidd / Moonraker UI button styles (optional enhancement)
python3 -c "
import urllib.request, json
try:
    url = 'http://127.0.0.1:7125/server/database/item?namespace=fluidd&key=macros'
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=3) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    macro_list = data.get('result', {}).get('value', [])
    if isinstance(macro_list, list):
        target_keys = {m['name'] for m in macro_list if 'name' in m}
        mods = [
            {'name': 'canhsathinhsu', 'categoryId': '0', 'disabledWhilePrinting': False, 'alias': '🚓 POLICE STROBE', 'color': 'error', 'visible': True},
            {'name': 'discodance', 'categoryId': '0', 'disabledWhilePrinting': False, 'alias': '🪩 DISCO DANCE', 'color': 'primary', 'visible': True},
            {'name': 'rgb_rainbow', 'categoryId': '0', 'disabledWhilePrinting': False, 'alias': '🌈 RAINBOW WAVE', 'color': 'secondary', 'visible': True},
            {'name': 'rgb_auto', 'categoryId': '0', 'disabledWhilePrinting': False, 'alias': '⚡ AUTO MODE', 'color': 'info', 'visible': True},
            {'name': 'rgb_off', 'categoryId': '0', 'disabledWhilePrinting': False, 'alias': '🛑 LED OFF', 'color': 'warning', 'visible': True}
        ]
        updated = False
        for mod in mods:
            existing = next((m for m in macro_list if m.get('name') == mod['name']), None)
            if existing:
                existing.update(mod)
                updated = True
            else:
                macro_list.append(mod)
                updated = True
        if updated:
            post_req = urllib.request.Request(
                'http://127.0.0.1:7125/server/database/item',
                data=json.dumps({'namespace': 'fluidd', 'key': 'macros', 'value': macro_list}).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            urllib.request.urlopen(post_req, timeout=3)
            print('[OK] Đã làm đẹp nút bấm Macro trên Fluidd UI')
except Exception as e:
    pass
" || true

# 7. Restart Klipper
echo -e "${YELLOW}[*] Đang khởi động lại dịch vụ Klipper...${NC}"
if command -v systemctl &> /dev/null; then
    sudo systemctl restart klipper || true
else
    curl -s -X POST http://127.0.0.1:7125/printer/restart || true
fi

sleep 2

# 8. Anonymous install counter
curl -s "https://abacus.jasoncameron.dev/hit/tonngodoc-qidi-plus5-rgb/installs" > /dev/null 2>&1 || true

echo -e "\n${GREEN}=====================================================${NC}"
echo -e "${GREEN}   🎉 CÀI ĐẶT THÀNH CÔNG MOD RGB CHO QIDI PLUS 5!   ${NC}"
echo -e "${GREEN}=====================================================${NC}"
echo -e "Bạn có thể điều khiển trực tiếp trên Fluidd Dashboard hoặc G-code:"
echo -e "  - ${BLUE}🚓 CANHSATHINHSU${NC} : Chớp kép Trái Xanh - Phải Đỏ x 10 lần (10s)"
echo -e "  - ${BLUE}🪩 DISCODANCE${NC}    : Chớp kép Xanh Đỏ + giật đèn thùng máy x 10 lần (10s)"
echo -e "  - ${BLUE}🌈 RGB_RAINBOW${NC}   : Cầu vồng 7 màu lượn sóng (giữ sáng cả khi màn hình ngủ)"
echo -e "  - ${BLUE}⚡ RGB_AUTO${NC}      : Chế độ LED tự động mặc định theo trạng thái in"
echo -e "  - ${BLUE}🛑 RGB_OFF${NC}       : Tắt hoàn toàn dải LED gầm"
echo -e "=====================================================\n"
