
⚡✨🔥💥

Cách chơi: [Cửa cược]  [Số tiền]
Cửa cược: - T/X/C/L
- Bot trả lời mới được tính là hợp lệ
- Tiền cược tối thiểu 5.000
- Lệch cửa tối đa 500.000

Tất cả người chơi có 100s để cược
- 100s của kỳ XX #447 bắt đầu

Xin mời đặt cược cho kỳ tung XX #447
VD: T 50000 hoặc C 30000
- Bot trả lời mới được tính là hợp lệ
- Tiền cược tối thiểu 5.000
- Lệch cửa tối đa 500.000
MD5: 895497e70c593151a805472896121e62
Tất cả người chơi có 100s để cược
- 100s của kỳ XX #447 bắt đầu

Xin mời đặt cược phiên #29561
Cách chơi: [Cửa cược]  [Số tiền]
Cửa cược: - T/X/C/L
- D1, D2,... D6
- SB3, SB4,... SB17, SB18
- TC/TL/XC/XL
MD5: 2519a559c16573e68b26f65be79a07c33


context.bot.send_message(
    chat_id=TAIXIU_GROUP_ID,
    text=(f"<b>Mời Bạn Đặt Cược Phiên</b> #{phien_number} 🕹\n\n"
          f"<blockquote><b>Cách chơi :</b> Cách chơi: [Cửa cược]  [Số tiền]\n"
          f"Cửa cược: - T/X/C/L</blockquote>\n"
          f"VD: T 50000 / X 50000 / C 50000 / L 50000</blockquote>\n\n"
          f"<b>- Bot trả lời mới được tính là hợp lệ</b>\n"
          f"<b>- Tiền cược tối thiểu 1.000</b>\n"
          f"<b>- Tiền cược tối đa 200.000</b></blockquote>\n"
          f"<blockquote>🎏 <b>Cược tối thiểu :</b> 1.000 VND</blockquote>\n"
          f"<b>Tất cả người chơi có 60s để cược</b>\n\n"
          f"- 60s của kỳ XX #447 bắt đầu !\n"),
    parse_mode='HTML',
    reply_markup=InlineKeyboardMarkup([[
        InlineKeyboardButton("Cược Ẩn Danh 👥",
                             url='https://t.me/botTX1_bot')
    ]]))

threading.Thread(target=start_taixiu_timer, args=(update, context)).start()