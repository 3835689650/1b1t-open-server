import datetime

print("=" * 40)
print("         祝 福 生 成 器")
print("=" * 40)
print("输入祝福语:")
a = input()
print("给谁(名字):")
b = input()
print("署名(你的名字):")
c = input()

now = datetime.datetime.now()
date_str = now.strftime("%Y年%m月%d日")
card = f"""
╔══════════════════════════════════╗
║                                  ║
║   Dear {b}:                       ║
║                                  ║
║   {a}                             ║
║                                  ║
║         —— {c} · {date_str}       ║
╚══════════════════════════════════╝
"""
print(card)
print("祝福已生成! 复制上面的卡片发给", b, "吧~")
print()
input("按回车键退出...")
