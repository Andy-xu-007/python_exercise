while True:
    txt = input('请输入一个数字：')
    if txt == 'stop':
        break
    elif not txt.isdigit():
        print('您输入的不是数字！\t')
    else:
        num = int(txt)
        if num < 20:
            print('您输入放入数字太小了！')
        elif num > 20:
            print('您输入放入数字太大了！')
        else:
            print('恭喜您，猜对啦！')

