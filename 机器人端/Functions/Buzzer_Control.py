import sys
import time
import hiwonder.Board as Board

Board.setBuzzer(0) # 关闭
Board.setBuzzer(1) # 打开
time.sleep(0.1) # 延时
Board.setBuzzer(0) # 关闭

time.sleep(1) # 延时

Board.setBuzzer(1)
time.sleep(0.5)
Board.setBuzzer(0)