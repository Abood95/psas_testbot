#!/usr/bin/env python2
# Python libs
import math

# Ros libs
import rospy

# Ros messages
from std_msgs.msg import Float64
from std_msgs.msg import Float32MultiArray
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Twist

LOOP_RATE_IN_HZ = 100
G = 9.81

if rospy.has_param('/use_simulation'):
	SIMULATION = rospy.get_param('/use_simulation')
	if SIMULATION:
		OFFSET_Y = 0.0
	else:
		OFFSET_Y = 0.135
else:
	SIMULATION = False
	OFFSET_Y = 0.135

class Controller:

	def __init__(self):

		self.gyro_x = 0.0
		self.gyro_y = 0.0
		self.gyro_z = 0.0

		self.accel_x = 0.0
		self.accel_y = 0.0
		self.accel_z = 0.0

		self.l1 = 0.79
		self.l2 = 31.2

		self.k1 = 0.4
		self.k2 = 0.899

		self.alpha = 0.0

		self.u = 0.0
		self.alphaB = [0.0, 0.0]
		self.psiB = [0.0, 0.0]
		self.delta1 = 0.0

		self.dt = 1.0 / LOOP_RATE_IN_HZ
		rospy.loginfo("dt = %f", self.dt)
		rospy.loginfo(SIMULATION)

		if SIMULATION:
			self.imu_sub = rospy.Subscriber('/imu', Imu, self.imu_callback)
		else:
			self.imu_sub = rospy.Subscriber('/testbot/imu', Float32MultiArray, self.imu_callback)

		self.delta1_pub = rospy.Publisher('/testbot/delta1', Float64, queue_size=10)
		self.u_pub = rospy.Publisher('/controller/u', Float64, queue_size=10)
		self.alphaB_pub = rospy.Publisher('/controller/alphaB', Float64, queue_size=10)
		self.psiB_pub = rospy.Publisher('/controller/psiB', Float64, queue_size=10)
		self.alpha_pub = rospy.Publisher('/controller/alpha', Float64, queue_size=10)
		self.vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=1)

		rospy.on_shutdown(self.shutdown)

	def control(self):
		self.alpha = math.asin(self.accel_y/G)

		self.alphaB.insert(0, (self.alphaB[0] + 0.005 * self.psiB[0] + self.l1 * (self.alpha - self.alphaB[0])))
		del self.alphaB[-1]

		# verschobener Index bei alphaB weil vorher insert an stelle 0
		self.psiB.insert(0, (self.psiB[0] + 0.01 * self.u + self.l2 * (self.alpha - self.alphaB[1])))
		del self.psiB[-1]
 
		self.u = -self.k1 * self.alphaB[1] - self.k2 * self.psiB[1]
		self.delta1 = math.tan(0.015 / 0.05 * self.u) * 180.0 / math.pi
		#self.delta1 = 0.0
		#rospy.loginfo(self.delta1)
		rospy.loginfo("alpha = %f", self.alpha)

	def publish_all(self):
		self.delta1_pub.publish(self.delta1)
		self.u_pub.publish(self.u)
		self.alphaB_pub.publish(self.alphaB[1])
		self.psiB_pub.publish(self.psiB[1])
		self.alpha_pub.publish(self.alpha)

	def imu_callback(self, msg):
		if SIMULATION:
			self.gyro_x = msg.angular_velocity.x
			self.gyro_y = -msg.angular_velocity.y
			self.gyro_z = -msg.angular_velocity.z
			self.accel_x = msg.linear_acceleration.x
			self.accel_y = -msg.linear_acceleration.y
			self.accel_z = -msg.linear_acceleration.z
			#rospy.loginfo("lin_accel_x = %f", self.accel_x)
			#rospy.loginfo("lin_accel_y = %f", self.accel_y)
			#rospy.loginfo("lin_accel_z = %f", self.accel_z)
		else:
			self.gyro_x = msg.data[0]
			self.gyro_y = msg.data[1]
			self.gyro_z = msg.data[2]
			self.accel_x = msg.data[3]
			self.accel_y = msg.data[4]
			self.accel_z = msg.data[5]

	def shutdown(self):
		msg = Twist()
		msg.linear.x = 0.0
		msg.angular.z = 0.0
		self.vel_pub.publish(msg)
		#rospy.loginfo("Controller is shut down")

def talker():
	rospy.init_node('controller', anonymous=True)
	ctrl = Controller()
	rate = rospy.Rate(LOOP_RATE_IN_HZ)
	while not rospy.is_shutdown():
		ctrl.control()
		ctrl.publish_all()
		rate.sleep()
	msg = Twist()
	msg.linear.x = 0.0
	vel_pub.publish(msg)

if __name__ == '__main__':
    try:
        talker()
    except rospy.ROSInterruptException: pass