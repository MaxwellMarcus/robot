from tkinter import *
import math
import sys
import time
import MPU6050 as mpu

root = Tk()
canvas = Canvas(width = 1500, height = 1000)
canvas.pack()

l_map = {'xy': 0, 'yz': 1, 'zx': 2}
mult_map = {'xy': [1, 1, 0], 'yz': [0, 1, 1], 'zx': [1, 0, 1]}

class Mass:
		def __init__(self, x, y, z, m):
				self.x, self.y, self.z, self.m = x, y, z, m
				self.joints = []
				self.pivot_joint = None
		def set_joint(self, j):
				self.joints.append(j)
				
		def set_as_pivot(self, j):
				self.pivot_joint = j

		def set_pos(self, x, y, z, dir):
				#print('pivot x, y, z: ', int(x), int(y), int(z))
				self.x, self.y, self.z = x, y, z

				for j in self.joints:
						#j.anchor_a[dir] = a + j.anchor_a.original[dir]
						j.set_pos(*j.anchor_a.get_pos(j.anchor_dist, *self.get_pos()), dir)
						# j.set_pos(self.x + j.anchor_dist * math.cos(j.anchor_a), self.y + j.anchor_dist * math.sin(j.anchor_a))

		def get_pos(self):
				return self.x, self.y, self.z


class Joint:
		def __init__(self, x, y, z, anchor, pivot):
				self.x, self.y, self.z, self.anchor, self.pivot = x, y, z, anchor, pivot

				self.anchor.set_joint(self)
				self.pivot.set_as_pivot(self)

				self.pivot_dist = Dist(self, pivot) #math.sqrt((self.x - self.pivot.x) ** 2 + (self.y - self.pivot.y) ** 2 + (self.z - self.pivot.z) ** 2)
				self.anchor_dist = Dist(self, pivot) #math.sqrt((self.x - self.anchor.x) ** 2 + (self.y - self.anchor.y) ** 2 + (self.z - self.anchor.z) ** 2)
		
				prev = None
				if self.anchor.pivot_joint:
						prev = self.anchor.pivot_joint.pivot_a
				#print(prev)
				self.anchor_a = Angle(self.anchor.x, self.anchor.y, self.anchor.z, self.x, self.y, self.z, prev)
				
				
				self.pivot_a = Angle(self.x, self.y, self.z, self.pivot.x, self.pivot.y, self.pivot.z, self.anchor_a)

		def set_a(self, a, dir):
				self.pivot_a[dir] = a
				# self.pivot.set_pos(*self.pivot_a.get_pos())
				self.pivot.set_pos(*self.pivot_a.get_pos(self.pivot_dist, *self.get_pos()), dir)

		def set_pos(self, x, y, z, dir):
				self.x, self.y, self.z = x, y, z
				self.pivot.set_pos(*self.pivot_a.get_pos(self.pivot_dist, *self.get_pos()), dir)

		def get_pos(self):
				return self.x, self.y, self.z
				

class Dist:
		def __init__(self, a, b):
				self.x, self.y, self.z = b.x - a.x, b.y - a.y, b.z - a.z
				self.d = math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

		def __mul__(self, a):
				return self.d * a

		def __rmul__(self, a):
				return self.d * a


class Angle:
		def __init__(self, x, y, z, x1, y1, z1, prev=None):
				self.prev = prev
				
				x, y, z = x1 - x, y1 - y, z1 - z
				r = math.sqrt(x ** 2 + y ** 2 + z ** 2)
				self.abs_theta = math.atan2(y, x)
				try: self.abs_phi = math.asin(z / r)
				except: self.abs_phi = 0
				
				if self.prev:
						self.theta = self.abs_theta - self.prev.abs_theta
						#print(round(math.degrees(self.abs_theta), 1), round(math.degrees(self.prev.abs_theta), 1))
						self.phi = self.abs_phi - self.prev.abs_phi
				else: self.theta, self.phi = self.abs_theta, self.abs_phi

		def get_rel_pos(self, d, x, y, z):
				return [
								x + d * math.cos(self.theta) * math.cos(self.phi),
								y + d * math.sin(self.theta) * math.cos(self.phi),
								z + d * math.sin(self.phi)
							 ]#[x + self.get_x(d), y + self.get_y(d), z + self.get_z(d)]
							 
		def get_pos(self, d, x, y, z):
				p = self.prev
				
				#print('------------------------')
				theta, phi = self.theta, self.phi
				#print(round(theta, 3))
				while p:
						theta, phi = theta + p.theta, phi + p.phi
				 #	 print(round(theta, 3), round(p.theta, 3))
						p = p.prev
						
				self.abs_theta, self.abs_phi = theta, phi
			 # print('Abs Theta, Theta: ', round(math.degrees(theta), 3), round(math.degrees(self.theta), 3))
						
				return [
								x + d * math.cos(theta) * math.cos(phi),
								y + d * math.sin(theta) * math.cos(phi),
								z + d * math.sin(phi)
							 ]

		def __getitem__(self, dir):
				if dir == 0: return self.theta
				else: return self.phi

		def __setitem__(self, dir, i):
				if dir == 0: self.theta = i
				else: self.phi = i




def get_center(canvas, *args):
		x, y, z = 0, 0, 0
		t = 0

		for i in args:
				x += i.x * i.m
				y += i.y * i.m
				z += i.z * i.m
				t += i.m

		return x / t, y / t, z / t

def mouse_press(event, j):
		global dir
		x, y = (event.x - centers[0][0]) / 20 - j.x, (event.y - centers[0][1]) / 20 - j.y
		sin_t = max([-1, min([1, x / 10])])
		sin_p = max([-1, min([1, y / 10])])
		t = math.asin(sin_t)
		p = math.asin(sin_p)
		j.set_a(t, 0)
		j.set_a(p, 1)

		# print('theta, phi: ', round(math.degrees(t), 3), round(math.degrees(p), 3))

def key_press(event):
		global dir
		if event.keysym == 'w':dir = (dir + 1) % 3
		if event.keysym == 's':dir = (dir - 1) % 3
		
		# d = 1
		# if event.keysym == 'a': j1.set_a(j1.pivot_a[d] + 0.1, d)
		# if event.keysym == 'd': j1.set_a(j1.pivot_a[d] - 0.1, d)
		
		# print('	 Relative, Absolute')
		# print('A1', round(math.degrees(j1.anchor_a.theta), 1), round(math.degrees(j1.anchor_a.abs_theta), 1))
		# print('P1', round(math.degrees(j1.pivot_a.theta), 1), round(math.degrees(j1.pivot_a.abs_theta), 1))
		# print('A2', round(math.degrees(j2.anchor_a.theta), 1), round(math.degrees(j2.anchor_a.abs_theta), 1))
		# print('P2', round(math.degrees(j2.pivot_a.theta), 1), round(math.degrees(j2.pivot_a.abs_theta), 1))

def render_mass(i, center, scale, dir, canvas):
		if dir == 0: x, y, w = i.x, i.y, (i.m - i.z) * scale
		elif dir == 1: x, y, w = i.z, i.y, (i.m - i.z) * scale
		else: x, y, w = i.x, -i.z, (i.m - i.y) * scale

		cx, cy = center
		ox, oy = (x * 10 * scale), (y * 10 * scale)

		canvas.create_rectangle(cx + ox + w, cy + oy + w, cx + ox - w, cy + oy - w)

def render_joint(i, center, scale, dir, canvas):
		if dir == 0: x, y, ax, ay, px, py	= i.x, i.y, i.anchor.x, i.anchor.y, i.pivot.x, i.pivot.y
		elif dir == 1: x, y, ax, ay, px, py = i.z, i.y, i.anchor.z, i.anchor.y, i.pivot.z, i.pivot.y
		else: x, y, ax, ay, px, py = i.x, -i.z, i.anchor.x, -i.anchor.z, i.pivot.x, -i.pivot.z

		cx, cy = center
		ox, oy = (x * 10 * scale), (y * 10 * scale)
		oax, oay = (ax * 10 * scale), (ay * 10 * scale)
		opx, opy = (px * 10 * scale), (py * 10 * scale)

		canvas.create_rectangle(cx + ox + 2, cy + oy + 2, cx + ox - 2, cy + oy - 2, outline='blue')
		canvas.create_line(cx + ox, cy + oy, cx + oax, cy + oay)
		canvas.create_line(cx + ox, cy + oy, cx + opx, cy + opy)

def render_center(cm, center, dir, scale, canvas):
		cmx, cmy, cmz = cm
		if dir == 0: x, y, m = cmx, cmy, (15 - cmz) / (1 / scale)
		elif dir == 1: x, y, m = cmz, cmy, (15 - cmx) / (1 / scale)
		else: x, y, m = cmx, -cmz, (15 - cmy) / (1 / scale)
		x, y = x * 10 * scale + center[0], y * 10 * scale + center[1]
		canvas.create_rectangle(x - m, y - m, x + m, y + m, outline='green')

dir = 0
cdir = 0

base = Mass(35, 30.5, 181.475, 0)
hip = Mass(35, 30.5, 181.475, 35)
leg_1_hip_servo2 = Mass(3.253, 24.427, 156.252, 12)
leg_1_upper = Mass(-16.41, 20, 95.437, 19)
leg_1_lower = Mass(4.954, 17.833, 34.483, 9)
leg_2_hip_servo2 = Mass(66.684, 24.427, 156.252, 12)
leg_2_upper = Mass(86.41, 20, 95.437, 19)
leg_2_lower = Mass(65.046, 17.833, 34.483, 9)

base_joint = Joint(35, 30.5, 181.475, base, hip)

leg_1_hip_servo_joint = Joint(4.45, 25.25, 167.875, hip, leg_1_hip_servo2)
leg_1_hip_servo2_joint = Joint(-11.1, 20, 154.735, leg_1_hip_servo2, leg_1_upper)
leg_1_hip_upper_joint = Joint(-1, 20, 80, leg_1_upper, leg_1_lower)
leg_2_hip_servo_joint = Joint(65.55, 25.25, 167.875, hip, leg_2_hip_servo2)
leg_2_hip_servo2_joint = Joint(81.1, 20, 154.735, leg_2_hip_servo2, leg_2_upper)
leg_2_hip_upper_joint = Joint(71, 20, 80, leg_2_upper, leg_2_lower)

arm_base_servo2 = Mass(33.866, 35.52, 206.698, 12)
arm_mid_servo = Mass(15.365, 40.825, 273.117, 16)
arm_mid_servo2 = Mass(41.173, 34.927, 301.059, 12)
arm_top = Mass(41.468, 30.353, 357.687, 25)

arm_base_servo_joint = Joint(35, 35.75, 195.075, hip, arm_base_servo2)
arm_base_servo2_joint = Joint(19.45, 41, 208.225, arm_base_servo2, arm_mid_servo)
arm_mid_servo_joint = Joint(29.55, 35.75, 299.925, arm_mid_servo, arm_mid_servo2)
arm_mid_servo2_joint = Joint(42.7, 30.5, 315.475, arm_mid_servo2, arm_top)

# m1 = Mass(0, 0, 0, 100)
# m2 = Mass(100, 200, 0, 100)
# m3 = Mass(300, 100, 0, 100)

# j1 = Joint(0, 100, 0, m1, m2)
# j2 = Joint(200, 100, 0, m2, m3)


# ms = [m1, m2, m3]
# js = [j1, j2]


ms = [
				base,
				hip,
				# leg_1_hip_servo,
				leg_1_hip_servo2,
				leg_1_upper,
				leg_1_lower,
				# leg_2_hip_servo,
				leg_2_hip_servo2,
				leg_2_upper,
				leg_2_lower,
				arm_base_servo2,
				arm_mid_servo,
				arm_mid_servo2,
				arm_top
		 ]
js = [
				base_joint,
				leg_1_hip_servo_joint,
				leg_1_hip_servo2_joint,
				leg_1_hip_upper_joint,
				leg_2_hip_servo_joint,
				leg_2_hip_servo2_joint,
				leg_2_hip_upper_joint,
				arm_base_servo_joint,
				arm_base_servo2_joint,
				arm_mid_servo_joint,
				arm_mid_servo2_joint
		 ]

centers = [[500, 500], [1250, 250], [1250, 750]]

colors = [['green', 'blue'], ['green', 'red'], ['red', 'blue']]


#root.bind('<Button-1>', lambda e: mouse_press(e, j1))
#root.bind('<Button-2>', lambda e: mouse_press(e, j2))
#root.bind('<Button-3>', lambda e: mouse_press(e, j3))

root.bind('<KeyPress>', key_press)

t = time.time()

x, y, z = 0, 0, 0

while True:
#	 print('------------------------')
 
	#Update
	
	dt = time.time() - t
	t = time.time()
	
	gx, gy, gz = mpu.read_gyro()
	x, y, z = x + (gx * dt), y + (gy * dt), z + (gz * dt)

	base_joint.set_a(math.radians(x), 0)
	base_joint.set_a(math.radians(y), 0)
	
	#---------------------
	#Render

	canvas.delete(ALL)

	canvas.create_text(10, 10, anchor='nw', text='{}, {}'.format(dir, cdir))

	canvas.create_line(1000, 0, 1000, 1000)
	canvas.create_line(1000, 500, 1500, 500)

	canvas.create_line(900, 50, 900, 150, fill=colors[dir][0])
	canvas.create_line(850, 100, 950, 100, fill=colors[dir][1])

	canvas.create_line(1450, 75, 1450, 125, fill=colors[(dir + 1) % 3][0])
	canvas.create_line(1425, 100, 1475, 100, fill=colors[(dir + 1) % 3][1])

	canvas.create_line(1450, 575, 1450, 625, fill=colors[(dir + 2) % 3][0])
	canvas.create_line(1425, 600, 1475, 600, fill=colors[(dir + 2) % 3][1])

	for i in ms:
		render_mass(i, centers[0], 0.12, dir, canvas)
		render_mass(i, centers[1], 0.06, (dir + 1) % 3, canvas)
		render_mass(i, centers[2], 0.06, (dir + 2) % 3, canvas)

	for i in js:
		render_joint(i, centers[0], 0.12, dir, canvas)
		render_joint(i, centers[1], 0.06, (dir + 1) % 3, canvas)
		render_joint(i, centers[2], 0.06, (dir + 2) % 3, canvas)

	cm = get_center(canvas, *ms)
	render_center(cm, centers[0], dir, 2, canvas)
	render_center(cm, centers[1], (dir + 1) % 3, 1, canvas)
	render_center(cm, centers[2], (dir + 2) % 3, 1, canvas)

	root.update()
