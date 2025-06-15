#!/usr/bin/python3
# coding=utf8
import sys
import time
import math
import hiwonder.Mpu6050 as Mpu6050
import hiwonder.ActionGroupControl as AGC

mpu = Mpu6050.mpu6050(0x68)#启动Mpu6050
mpu.set_gyro_range(mpu.GYRO_RANGE_2000DEG)#设置Mpu6050的陀螺仪的工作范围
mpu.set_accel_range(mpu.ACCEL_RANGE_2G)#设置Mpu6050的加速度计的工作范围

count1 = 0
count2 = 0

def standup():
    global count1, count2 
    
    try:
        accel_date = mpu.get_accel_data(g=True) #获取传感器值
        angle_y = int(math.degrees(math.atan2(accel_date['y'], accel_date['z']))) #将获得的数据转化为角度值
        
        if abs(angle_y) > 160: #y轴角度大于160，count1加1，否则清零
            count1 += 1
        else:
            count1 = 0

        if abs(angle_y) < 10: #y轴角度小于10，count2加1，否则清零
            count2 += 1
        else:
            count2 = 0

        time.sleep(0.1)
        
        if count1 >= 5: #往前倒了一定时间后起来
            count1 = 0  
            print("stand up back！")#打印执行的动作名
            AGC.runActionGroup('stand_up_back')#执行动作
        
        elif count2 >= 5: #往后倒了一定时间后起来
            count2 = 0
            print("stand up front！")#打印执行的动作名
            AGC.runActionGroup('stand_up_front')#执行动作            
        
    except BaseException as e:
        print(e)

if __name__ == '__main__':
    print("Fall_and_Stand Init")
    print("Fall_and_Stand Start")
    while True :#循环检测机器人的状态
        standup()
        key = time.sleep(0.1)
        if key == 27:
            break
        
