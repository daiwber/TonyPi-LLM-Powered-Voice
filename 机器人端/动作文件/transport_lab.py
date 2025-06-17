import time
import hiwonder.Board as Board

# 假设舵机1控制头部上下运动，舵机2控制头部左右运动
SERVO_UP_DOWN = 1  # 头部上下舵机编号
SERVO_LEFT_RIGHT = 2  # 头部左右舵机编号

# 初始脉冲宽度（对应中间位置）
pulse_up_down = 500  # 初始脉冲宽度，对应头部中间位置（不抬头也不低头）
pulse_left_right = 500  # 初始脉冲宽度，对应头部中间位置（不左转也不右转）

# 设置头部初始位置
Board.setPWMServoPulse(SERVO_UP_DOWN, pulse_up_down, 500)
Board.setPWMServoPulse(SERVO_LEFT_RIGHT, pulse_left_right, 500)
time.sleep(0.5)

# 头部向上抬头
pulse_up_down += 50  # 增加脉冲宽度，使头部向上抬头
Board.setPWMServoPulse(SERVO_UP_DOWN, pulse_up_down, 500)
time.sleep(1)

# 头部向下低头
pulse_up_down -= 50  # 减少脉冲宽度，使头部向下低头
Board.setPWMServoPulse(SERVO_UP_DOWN, pulse_up_down, 500)
time.sleep(1)

# 头部向左转
pulse_left_right -= 50  # 减少脉冲宽度，使头部向左转
Board.setPWMServoPulse(SERVO_LEFT_RIGHT, pulse_left_right, 500)
time.sleep(1)

# 头部向右转
pulse_left_right += 50  # 增加脉冲宽度，使头部向右转
Board.setPWMServoPulse(SERVO_LEFT_RIGHT, pulse_left_right, 500)
time.sleep(1)

# 回到初始位置
pulse_up_down = 500
pulse_left_right = 500
Board.setPWMServoPulse(SERVO_UP_DOWN, pulse_up_down, 500)
Board.setPWMServoPulse(SERVO_LEFT_RIGHT, pulse_left_right, 500)
time.sleep(0.5)