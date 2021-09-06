from tkinter import *
import math
import sys
import time
import numpy as np
# import servo_control as servo
# import MPU6050 as mpu
import graphics

class Mass:
		def __init__(self, x, y, z, m):
				self.x, self.y, self.z, self.m = x, y, z, m

				self.abs_x, self.abs_y, self.abs_z = x, y, z

				self.joints = []
				self.pivot_joint = None
		def set_joint(self, j):
				self.joints.append(j)

		def set_as_pivot(self, j):
				self.pivot_joint = j

		def set_pos(self, x, y, z):
				self.x, self.y, self.z = x, y, z

				for j in self.joints:
						j.set_pos(*j.anchor_a.get_pos(j.anchor_dist, *self.get_pos()))

		def get_pos(self):
				return self.x, self.y, self.z


class Joint:
		def __init__(self, x, y, z, anchor, pivot, prev=None):
				self.x, self.y, self.z, self.anchor, self.pivot = x, y, z, anchor, pivot

				self.anchor.set_joint(self)
				self.pivot.set_as_pivot(self)

				self.pivot_dist = dist(self, pivot)
				self.anchor_dist = dist(self, anchor)

				if not prev:
					if self.anchor.pivot_joint:
						prev = self.anchor.pivot_joint.pivot_a
					else: prev = None

				self.anchor_a = Angle(self.anchor.x, self.anchor.y, self.anchor.z, self.x, self.y, self.z, prev)
				self.pivot_a = Angle(self.x, self.y, self.z, self.pivot.x, self.pivot.y, self.pivot.z, self.anchor_a)

		def set_a(self, a, dir):
				self.pivot_a[dir] = a
				self.pivot.set_pos(*self.pivot_a.get_pos(self.pivot_dist, *self.get_pos()))

		def set_pos(self, x, y, z):
				self.x, self.y, self.z = x, y, z
				self.pivot.set_pos(*self.pivot_a.get_pos(self.pivot_dist, *self.get_pos()))

		def get_pos(self):
				return self.x, self.y, self.z

def dist(a, b):
	x, y, z = b.x - a.x, b.y - a.y, b.z - a.z
	return math.sqrt(x ** 2 + y ** 2 + z ** 2)



class Angle:
		def __init__(self, x, y, z, x1, y1, z1, prev=None):
			self.prev = prev

			x, y, z = x1 - x, y1 - y, z1 - z
			r = math.sqrt(x ** 2 + y ** 2 + z ** 2)
			self.theta = math.atan2(y, z)
			try: self.psi = math.asin(x / r)
			except: self.psi = 0
			self.phi = 0

			self.pos_to_rotation_matrix(x, y, z)

			self.abs_x, self._abs_y, self.abs_z = x, y, z
			self.abs_Rx, self.abs_Ry, self.abs_Rz, self.abs_rotation_matrix = np.copy(self.Rx), np.copy(self.Ry), np.copy(self.Rz), np.copy(np.dot(np.dot(self.Rz, self.Rx), self.Ry))

		def get_rel_pos(self, d, x, y, z):
			return [
			x + d * math.cos(self.theta) * math.cos(self.phi),
			y + d * math.sin(self.theta) * math.cos(self.phi),
			z + d * math.sin(self.phi)
			]

		def get_pos(self, d, x, y, z):
			R = self.get_rotation_matrix()
			Rs = [self.get_rotation_matrix()]
			zero = np.array([d, 0, 0], 'float')
			pos = np.dot(R, zero)

			p = self.prev
			i = 0
			while p:
				Rs = [p.get_rotation_matrix()] + Rs
				p = p.prev
				i += 1

			R = Rs[0]
			for i in Rs[1:]:
				R = np.dot(R, i)

			pos = np.dot(R, zero)
			offset = np.array([x, y, z])
			return offset + pos

		def set_rotation_matrix(self, dir, i):
			if dir == 0:
				self.Rz = np.array([[math.cos(i), -math.sin(i), 0.0],
									[math.sin(i), math.cos(i), 0.0],
								 [0.0, 0.0, 1.0]], 'float')
			if dir == 1:
				self.Ry = np.array([[math.cos(i), 0.0, -math.sin(i)],
								 [0.0, 1.0, 0.0],
								 [math.sin(i), 0.0, math.cos(i)]], 'float')
			if dir == 2:
				self.Rx = np.array([[1.0, 0.0, 0.0],
								 [0.0, math.cos(i), -math.sin(i)],
								 [0.0, math.sin(i), math.cos(i)]], 'float')

			self.rotation_matrix = self.get_rotation_matrix()

		def get_rotation_matrix(self):
			R = np.dot(np.dot(self.Rz, self.Rx), self.Ry)
			if self.prev: return np.dot(self.prev.abs_rotation_matrix.T, R)
			else: return R

		def pos_to_rotation_matrix(self, x, y, z):
			r_xy = math.sqrt(x ** 2 + y ** 2)
			r = math.sqrt(x ** 2 + y ** 2 + z ** 2)

			if not r_xy == 0: self.Rz = np.array([[x / r_xy, -y / r_xy, 0.0],
									[y / r_xy, x / r_xy, 0.0],
								 [0.0, 0.0, 1.0]], 'float')
			else: self.Rz = np.eye(3)

			x, y, z = np.dot(self.Rz.T, np.array([x, y, z]))

			if not r == 0: self.Ry = np.array([[x / r, 0.0, -z / r],
								[0.0, 1.0, 0.0],
							 [z / r, 0.0, x / r]], 'float')
			else: self.Ry = np.eye(3)

			x, y, z = np.dot(np.transpose(self.Ry), np.array([x, y, z]))

			self.Rx = np.eye(3)

			self.rotation_matrix = self.get_rotation_matrix()

		def bring_to_axis(self, x, y, z):
			Rs = [self.get_rotation_matrix()]
			zero = np.array([x, y, z], 'float')

			p = self.prev
			i = 0
			while p:
				Rs = [p.get_rotation_matrix()] + Rs
				p = p.prev
				i += 1

			R = Rs[0]
			for i in Rs[1:]:
				R = np.dot(R, i)

			return np.dot(R, zero)
		def __getitem__(self, dir):
			if dir == 0: return self.theta
			if dir == 1: return self.phi
			return self.psi

		def __setitem__(self, dir, i):
			self.set_rotation_matrix(dir, i)
			if dir == 0: self.theta = i
			elif dir == 1: self.phi = i
			else: self.psi = i

def get_center(*args):
		x, y, z = 0, 0, 0
		t = 0

		for i in args:
				x += i.x * i.m
				y += i.y * i.m
				z += i.z * i.m
				t += i.m

		return x / t, y / t, z / t

def get_balance(m1, m2, fs1, fs2, x, y):
		if m1.abs_x < m2.abs_x: f1, f2 = fs1, fs2
		else: f1, f2 = fs2, fs1

		#0: - -
		#1: + -
		#2: - +
		#3: + +

		if f1[0].abs_y < f2[0].abs_y:
		    return [f1[0].x, f1[0].y, f1[1].x, f1[1].y, f2[1].x, f2[1].y, f2[3].x, f2[3].y, f2[2].x, f2[2].y, f1[2].x, f1[2].y]
		else:
		    return [f1[2].x, f1[2].y, f1[0].x, f1[0].y, f2[0].x, f2[0].y, f2[1].x, f2[1].y, f2[3].x, f2[3].y, f1[3].x, f1[3].y]

def in_balance(points, x, y):

	#Jordan's Theorum
	# Points in closed shape will intersect edges an odd number of times

	intersects = 0
	for i in range(0, len(points), 2):
		temp1 = [points[i], points[i + 1]]
		if not i + 2 >= len(points): temp2 = [points[i + 2], points[i + 3]]
		else: temp2 = [points[0], points[1]]
		if temp1[0] < temp2[0]: p1, p2 = temp1, temp2
		else: p1, p2 = temp2, temp1

		if (y >= p1[1] and y <= p2[1]) or (y <= p1[1] and y >= p2[1]):
			if p2[0] == p1[0]:
				intersection = p2[0]
			elif p2[1] == p1[1]:
				return False
			else:
				m = (p2[1] - p1[1]) / (p2[0] - p1[0])
				b = - (m * p1[0]) + p1[1]
				intersection = (y - b) / m


			if intersection > x:
				intersects += 1
	return intersects % 2 == 1

def get_feet(foot_1, foot_2, x, y):
	if foot_1.y < foot_2.y: f1, f2 = foot_2, foot_1
	else:  f1, f2 = foot_1, foot_2

	dx, dy = x - foot_1.x, y - foot_1.y

	return x + dx, y + dy

def move_leg(o_leg_1, o_leg_2, x, y, cmx, cmy):
    if o_leg_1[3].y < o_leg_2[3].y: leg_1, leg_2 = o_leg_2, o_leg_1
    else: leg_1, leg_2 = o_leg_1, o_leg_2


    #Leg Movement Directions:
    #0: Z
    #1: X
    #2: X
    dy = leg_2[1].y - leg_2[2].y
    dz = leg_2[1].z - leg_2[2].z

    upper_length = math.sqrt(dy ** 2 + dz ** 2)

    move_dist = y - cmy

    if abs(y - cmy) > abs(upper_length):
    	move_dist = upper_length

    psi = math.asin(move_dist / upper_length)

    # if leg_2[1].pivot_a.psi - psi > -0.1:
    # 	v = 0.01
    # else:
    # 	v = -0.01

    # leg_2[1].set_a(leg_2[1].pivot_a.psi + v, dir = 2)
    # leg_2[2].set_a(leg_2[2].pivot_a.psi - v, dir = 2)

    # leg_1[1].set_a(leg_1[1].pivot_a.psi - v, dir = 2)
    # leg_1[2].set_a(leg_1[2].pivot_a.psi + v, dir = 2)

    # servo.move_a(1, v)
    # servo.move_a(0, v)
    # servo.move_a(4, v)
    # servo.move_a(3, v)

    leg_2[1].set_a(psi, dir = 2)
    leg_2[2].set_a(-psi, dir = 2)

    leg_1[1].set_a(-psi, dir = 2)
    leg_1[2].set_a(psi, dir = 2)

    # servo.set_a(1, psi)
    # servo.set_a(0, psi)
    # servo.set_a(4, psi)
    # servo.set_a(3, psi)

def get_mass_render(i):
	return graphics.Cube(*i.get_pos(), 2)

def get_joint_render(i):
	return [
		graphics.Cube(*i.get_pos(), 1, color=[1, 0, 0]),
		graphics.Line(*i.anchor.get_pos(), *i.get_pos()),
		graphics.Line(*i.get_pos(), *i.pivot.get_pos())
	]

def get_center_render(cm):
	return graphics.Cube(*cm, 5, color=[0, 0, 1], projection=True)

def get_balance_render(coords, in_balance):
	return graphics.Polygon2D(coords, color = [0.75, 0, 1] if in_balance else [1, 0, 0.4])

def create_zeroed_joint(x, y, z, anchor, pivot, prev=None):
	m = Mass(x, y, z, 0)
	m1 = Mass(x, y, z, 0)
	j1 = Joint(*anchor.get_pos(), anchor, m, prev)
	j2 = Joint(x, y, z, m, m1)
	j3 = Joint(x, y, z, m1, pivot)
	return j1, j2, j3

dir = 0
cdir = 0

theta, phi, psi = 0, 0, 0

base = Mass(35, 30.5, 181.475, 0)
hip = Mass(35, 30.5, 181.475, 35)
leg_1_hip_servo2 = Mass(3.253, 24.427, 156.252, 12)
zero_mass_1 = Mass(*leg_1_hip_servo2.get_pos(), 1)
leg_1_upper = Mass(-16.41, 20, 95.437, 19)
leg_1_lower = Mass(4.954, 17.833, 34.483, 9)
leg_2_hip_servo2 = Mass(66.684, 24.427, 156.252, 12)
leg_2_upper = Mass(86.41, 20, 95.437, 19)
leg_2_lower = Mass(65.046, 17.833, 34.483, 9)

xr, yr = 4.5, 12

leg_1_foot = Mass(5, 10, 2.5, 1)
leg_1_foot_1 = Mass(5 - xr, 10 - yr, 2.5, 1)
leg_1_foot_2 = Mass(5 + xr, 10 - yr, 2.5, 1)
leg_1_foot_3 = Mass(5 - xr, 10 + yr, 2.5, 1)
leg_1_foot_4 = Mass(5 + xr, 10 + yr, 2.5, 1)

leg_2_foot = Mass(65, 10, 2.5, 1)
leg_2_foot_1 = Mass(65 - xr, 10 - yr, 2.5, 1)
leg_2_foot_2 = Mass(65 + xr, 10 - yr, 2.5, 1)
leg_2_foot_3 = Mass(65 - xr, 10 + yr, 2.5, 1)
leg_2_foot_4 = Mass(65 + xr, 10 + yr, 2.5, 1)

base_joint = Joint(35, 30.5, 181.475, base, hip)

leg_1_hip_servo_joint, zeroed_1_hip_servo, zero_mass_hip_1 = create_zeroed_joint(4.45, 25.25, 167.875, hip, leg_1_hip_servo2, prev=base_joint.pivot_a)
leg_1_hip_servo2_joint, zeroed_1_servo_upper, zero_mass_upper_1 = create_zeroed_joint(-11.1, 20, 154.735, leg_1_hip_servo2, leg_1_upper)
leg_1_hip_upper_joint, zeroed_1_upper_lower, zero_mass_lower_1 = create_zeroed_joint(-1, 20, 80, leg_1_upper, leg_1_lower)
leg_2_hip_servo_joint, zeroed_2_hip_servo, zero_mass_hip_2 = create_zeroed_joint(65.55, 25.25, 167.875, hip, leg_2_hip_servo2, prev=base_joint.pivot_a)
leg_2_hip_servo2_joint, zeroed_2_servo_upper, zero_mass_upper_2 = create_zeroed_joint(81.1, 20, 154.735, leg_2_hip_servo2, leg_2_upper)
leg_2_hip_upper_joint, zeroed_2_upper_lower, zero_mass_lower_2 = create_zeroed_joint(71, 20, 80, leg_2_upper, leg_2_lower)

# arm_base_servo2 = Mass(33.866, 35.52, 206.698, 12)
# arm_mid_servo = Mass(15.365, 40.825, 273.117, 16)
# arm_mid_servo2 = Mass(41.173, 34.927, 301.059, 12)
# arm_top = Mass(41.468, 30.353, 357.687, 100)#25)

# arm_base_servo_joint, zeroed_hip_arm, zero_mass_base = create_zeroed_joint(35, 35.75, 195.075, hip, arm_base_servo2, prev=base_joint.pivot_a)
# arm_base_servo2_joint, zeroed_base_mid, zero_mass_mid = create_zeroed_joint(19.45, 41, 208.225, arm_base_servo2, arm_mid_servo)
# arm_mid_servo_joint, zeroed_mid_mid, zero_mass_mid_2 = create_zeroed_joint(29.55, 35.75, 299.925, arm_mid_servo, arm_mid_servo2)
# arm_mid_servo2_joint, zeroed_mid_top, zero_mass_upper = create_zeroed_joint(42.7, 30.5, 315.475, arm_mid_servo2, arm_top)

leg_1_foot_joint = Joint(5, 10, 2.5, leg_1_lower, leg_1_foot)
leg_1_foot_joint_1 = Joint(5, 10, 2.5, leg_1_foot, leg_1_foot_1)
leg_1_foot_joint_2 = Joint(5, 10, 2.5, leg_1_foot, leg_1_foot_2)
leg_1_foot_joint_3 = Joint(5, 10, 2.5, leg_1_foot, leg_1_foot_3)
leg_1_foot_joint_4 = Joint(5, 10, 2.5, leg_1_foot, leg_1_foot_4)

leg_2_foot_joint = Joint(65, 10, 2.5, leg_2_lower, leg_2_foot)
leg_2_foot_joint_1 = Joint(65, 10, 2.5, leg_2_foot, leg_2_foot_1)
leg_2_foot_joint_2 = Joint(65, 10, 2.5, leg_2_foot, leg_2_foot_2)
leg_2_foot_joint_3 = Joint(65, 10, 2.5, leg_2_foot, leg_2_foot_3)
leg_2_foot_joint_4 = Joint(65, 10, 2.5, leg_2_foot, leg_2_foot_4)

m_render = [
	base,
	hip,
	leg_1_hip_servo2,
	leg_1_upper,
	leg_1_lower,
	leg_2_hip_servo2,
	leg_2_upper,
	leg_2_lower,
	# arm_base_servo2,
	# arm_mid_servo,
	# arm_mid_servo2,
	# arm_top,
	leg_1_foot_1,
	leg_1_foot_2,
	leg_1_foot_3,
	leg_1_foot_4,
	leg_2_foot_1,
	leg_2_foot_2,
	leg_2_foot_3,
	leg_2_foot_4,
]
m_calculate = [
	base,
	hip,
	leg_1_hip_servo2,
	leg_1_upper,
	leg_1_lower,
	leg_2_hip_servo2,
	leg_2_upper,
	leg_2_lower,
	# arm_base_servo2,
	# arm_mid_servo,
	# arm_mid_servo2,
	# arm_top,
	leg_1_foot,
	leg_2_foot,
]
js = [
	base_joint,
	leg_1_hip_servo_joint,
	leg_1_hip_servo2_joint,
	leg_1_hip_upper_joint,
	leg_2_hip_servo_joint,
	leg_2_hip_servo2_joint,
	leg_2_hip_upper_joint,
	zero_mass_hip_1,
	zero_mass_upper_1,
	zero_mass_lower_1,
	zero_mass_hip_2,
	zero_mass_upper_2,
	zero_mass_lower_2,
	# arm_base_servo_joint,
	# arm_base_servo2_joint,
	# arm_mid_servo_joint,
	# arm_mid_servo2_joint,
]

centers = [[500, 500], [1250, 250], [1250, 750]]

colors = [['green', 'blue'], ['green', 'red'], ['red', 'blue']]

t = time.time()

x, y, z = 0, 0, 0

while True:
	# print('------------------------')

	#Update

	dt = time.time() - t
	t = time.time()

	# gx, gy, gz = mpu.read_gyro()
	# x, y, z = x + (gx * dt), y + (gy * dt), z + (gz * dt)
	#
	# print(round(x), round(y), round(z))
	#
	# # 	base_joint.set_a(math.radians(x), 0)
	# # 	base_joint.set_a(math.radians(y), 1)
	# base_joint.set_a(math.radians(y), 2)

	graphics.on_key('i', lambda: base_joint.set_a(base_joint.pivot_a.psi + 0.1, 2))
	graphics.on_key('k', lambda: base_joint.set_a(base_joint.pivot_a.psi - 0.1, 2))

	cm = get_center(*m_calculate)

	if leg_1_foot.z - leg_2_foot.z > 1000:
		foot_1, foot_2 = leg_1_foot, leg_1_foot
		feet_1 = [leg_1_foot_1, leg_1_foot_2, leg_1_foot_3, leg_1_foot_4]
		feet_2 = feet_1
	elif leg_2_foot.z - leg_1_foot.z > 1000:
		foot_1, foot_2 = leg_2_foot, leg_2_foot
		feet_1 = [leg_2_foot_1, leg_2_foot_2, leg_2_foot_3, leg_2_foot_4]
		feet_2 = feet_1
	else:
		foot_1, foot_2 = leg_1_foot, leg_2_foot
		feet_1 = [leg_1_foot_1, leg_1_foot_2, leg_1_foot_3, leg_1_foot_4]
		feet_2 = [leg_2_foot_1, leg_2_foot_2, leg_2_foot_3, leg_2_foot_4]

	balance = get_balance(foot_1, foot_2, feet_1, feet_2, 7.5, 15)
	balanced = in_balance(balance, cm[0], cm[1])

	if not balanced:
		feet = get_feet(leg_1_foot, leg_2_foot, cm[0], cm[1])

		leg_1 = [
			zeroed_1_hip_servo,
			zeroed_1_servo_upper,
			zeroed_1_upper_lower,
			leg_1_foot,
		]
		leg_2 = [
			zeroed_2_hip_servo,
			zeroed_2_servo_upper,
			zeroed_2_upper_lower,
			leg_2_foot
		]


		move_leg(leg_1, leg_2, *feet, cm[0], cm[1])

	#---------------------
	#Render
	objects = []

	objects.append(get_balance_render(balance, balanced))
	objects.append(get_center_render(cm))

	for i in m_render:
		objects.append(get_mass_render(i))

	for i in js:
		objects += get_joint_render(i)

	graphics.render(objects)
