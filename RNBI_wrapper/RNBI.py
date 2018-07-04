import sys
import os
import math
import numpy as np
import copy
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from functools import reduce
import_dir = os.path.join(os.path.join(os.path.dirname(__file__),os.pardir),'mosek_wrapper')
sys.path.insert(0,import_dir)
file_name = 'mosek_g'
mosek_g = __import__(file_name)
file_name = 'mosek_linear'
mosek_linear = __import__(file_name)
file_name = 'mosek_quadratic'
mosek_quadratic = __import__(file_name)


class RNBI(object):
	def __init__(self, params):
		params = mosek_g.params_init(params)
		self.params = params
		self.params["minimize"] = True
		self.params["silent"] = True
		self.Y = params["Y"]
		self.dim = len(params["Y"])
		print(self.dim)
		self.anti_y = [0] * self.dim
		self.support_vector = [0] * self.dim
		self.boundary = []
		self.controlu = []
		self.v = []
		self.beta = None
		self.plane_pts = []					
		self.step_size = params.get("step_size", None)
		self.step_points = params.get("projection_points", 10)
		self.direction = params.get("direction", [1] * self.dim)
		for i in range(self.dim + 1):
			self.v.append([0]*self.dim)
	def control_2_state(self, x_vector):
		y_vector = []
		for y_k in self.Y:
			sum_tmp = 0
			for i in range(len(y_k)):
				sum_tmp += y_k[i] * x_vector[i]
			y_vector.append(sum_tmp)
		return y_vector

	def solve(self):
		self._get_yai()
		self._get_support_vector()
		self._get_vk()
		self._get_plane_pts()
		self._projection()
		self._examination()
		result = {
		"anti_y": self.anti_y,
		"support_vector" : self.support_vector,
		"boundary_points" : self.boundary,
		"control" : self.controlu,
		"v_points" : self.v,
		"reference_points": self.plane_pts
		}
		return result

	def _get_yai(self):
		points = []
		control = []
		for i in range(self.dim):
			C_obj = list(map(lambda x: x * self.direction[i], self.Y[i]))
			self.params["C_obj"] = C_obj
			pro = self.optimizer(self.params)
			code, result = pro.fit()
			if code == 0:
				control.append(result["x"])
				points.append(self.control_2_state(result["x"]))
			else:
				raise Exception("Wrong Optimization Defination")
		for pts in points:
			self.boundary.append(pts)
		for cts in control:
			self.controlu.append(cts)

		Yai = [0] * self.dim
		for i in range(self.dim):
			tmp = [0] * self.dim
			for j in range(self.dim):
				tmp[j] = points[j][i] * self.direction[i]
			Yai[i] = max(tmp) * self.direction[i]
		self.anti_y = Yai
		# for p in range(len(points)):
		# 	self.anti_y[p] = points[p - self.dim + 1][p]


	def _get_support_vector(self):
		C_obj = np.array([0]*len(self.params["bux"]),dtype=np.float64)
		for i in range(self.dim):
			C_obj += (np.array(self.Y[i], dtype=np.float64) * self.direction[i])
		C_obj = list(C_obj)
		self.params["C_obj"] = C_obj
		pro = self.optimizer(self.params)
		code, result = pro.fit()
		if code == 0:
			self.controlu.append(result["x"])
			self.support_vector = self.control_2_state(result["x"])
			self.beta = 0
			for i in range(self.dim):
				self.beta += self.support_vector[i] * self.direction[i]
			self.boundary.append(self.support_vector)
		else:
			raise Exception("Wrong Optimization Defination")

	def _get_vk(self):
		self.v[0] = self.anti_y
		if self.dim == 2:
			self.v[1] = [self.direction[0]*(self.beta - self.direction[1]*self.anti_y[1]), self.anti_y[1]]
			self.v[2] = [self.anti_y[0], self.direction[1]*(self.beta - self.direction[0]*self.anti_y[0])]
		if self.dim == 3:
			self.v[1] = [self.direction[0] * (self.beta - self.direction[1] * self.anti_y[1] - self.direction[2] * self.anti_y[2]), self.anti_y[1], self.anti_y[2]]
			self.v[2] = [self.anti_y[0], self.direction[1] * (self.beta - self.direction[0] * self.anti_y[0] - self.direction[2] * self.anti_y[2]), self.anti_y[2]]
			self.v[3] = [self.anti_y[0], self.anti_y[1], self.direction[2] * (self.beta - self.direction[0] * self.anti_y[0] - self.direction[1] * self.anti_y[1])]


	def _get_plane_pts(self):
		if self.dim == 2:
			v1 = np.array(self.v[1])
			v2 = np.array(self.v[2])

			v1_v2 = v2 - v1
			if self.step_size is None:
				pass
			else:
				self.step_points = max(1, int(self._distance(v1_v2)/self.step_size + 0.5))
			for i in range(self.step_points+1):
				self.plane_pts.append(list(v1 + v1_v2*i/self.step_points))
		elif self.dim == 3:
			v1 = np.array(self.v[1])
			v2 = np.array(self.v[2])
			v3 = np.array(self.v[3])
			v1_v2 = v2 - v1
			v1_v3 = v3 - v1
			if self.step_size is None:
				step_points_x = self.step_points
				step_points_y = self.step_points
			else:
				step_points_x = max(1, int(self._distance(v1_v2)/self.step_size + 0.5))
				step_points_y = max(1, int(self._distance(v1_v3)/self.step_size + 0.5))
			for i in range(step_points_x + 1):
				for j in range(step_points_y + 1):
					if 1.0*i/step_points_x + 1.0*j/step_points_y > 1:
						continue
					self.plane_pts.append(list(v1 + v1_v2*i/step_points_x + v1_v3*j/step_points_y))
	def _projection(self):
		for pts in self.plane_pts:
			obj = [0] * len(self.params['bux']) + [1]
			tmp_params = copy.deepcopy(self.params)
			tmp_params["C_obj"] = obj
			if tmp_params["A_con"] and len(tmp_params["A_con"])>0:
				for acon in tmp_params["A_con"]:
					acon.append(0)
			for i in range(self.dim):
				tmp_params["A_con"].append(self.Y[i] + [-1 * self.direction[i]])
				# tmp_params["A_con"].append(self.Y[i] + [-1 * self.direction[i]])
				if self.direction[i] == 1:
					tmp_params["buc"].append(pts[i])
					tmp_params["blc"].append(-mosek_g.INF)
				elif self.direction[i] == -1:
					tmp_params["buc"].append(mosek_g.INF)
					tmp_params["blc"].append(pts[i])
				if tmp_params.get("Q_con", None) is not None:
					tmp_params["Q_con"].append(None)

			max_t = mosek_g.INF
			# max_t = 10
			for v in self.v[1::]:
				max_t = min(self._distance(pts, v) + mosek_g.EPS, max_t)
			tmp_params["bux"].append(10)
			tmp_params["blx"].append(0)

			pro = self.optimizer(tmp_params)

			code, result = pro.fit()

			if code == 0:
				t = result["opti"]
				u = result["x"][0:-1]
				projection_point = list(np.array(pts)+ np.array(self.direction)*t)
				control_point = self.control_2_state(u)
				self.boundary.append(projection_point)
				self.controlu.append(u)
			else:
				pass
	def _examination(self):
		del_pts = []

		for pts_i, pts in enumerate(self.boundary, start=0):
			if pts_i < 1 + self.dim:
				continue
		# for pts_i, pts in enumerate([[-0.5278021417484701, -1.1026431196420385, 0.0]], start=0) :
			# outrange = False
			# for i in range(self.dim):
			# 	if pts[i] * self.direction[i] > self.anti_y[i]:
			# 		outrange = True
			# 		break	
			# if outrange:
			# 	del_pts.append(pts_i)
			# 	continue
			tmp_params = copy.deepcopy(self.params)
			C_obj = np.array([0]*len(self.params["bux"]), dtype=np.float64)
			for i in range(self.dim):
				C_obj += np.array(self.Y[i], dtype=np.float64) *self.direction[i]

			C_obj = list(C_obj)

			
			tmp_params["C_obj"] = C_obj
			for i in range(self.dim):
				tmp_params["A_con"].append(self.Y[i])
				if self.direction[i] == 1:
					tmp_params["buc"].append(pts[i] + mosek_g.EPS)
					tmp_params["blc"].append(-mosek_g.INF)
				elif self.direction[i] == -1:
					tmp_params["buc"].append(mosek_g.INF)
					tmp_params["blc"].append(pts[i] - mosek_g.EPS)
				if tmp_params.get("Q_con", None) is not None:
					tmp_params["Q_con"].append(None)

			pro = self.optimizer(tmp_params)
			code, result = pro.fit()
		
			y_tmp = [0] * self.dim
			if code == 0:
				variables = result["x"]
			else:
				del_pts.append(pts_i)
				continue
			for i in range(self.dim):
				for j in range(len(variables)):
					y_tmp[i] += variables[j]*self.Y[i][j]
			if self._distance(y_tmp, pts)> 0.01:
				del_pts.append(pts_i)
		del_pts = del_pts[::-1]

		for d in del_pts:
			del self.boundary[d]
			del self.controlu[d]

	def visual(self, ax):
		if self.dim == 2:
			ax.scatter(self.anti_y[0],self.anti_y[1],color='red',marker='x')
			ax.scatter(self.support_vector[0],self.support_vector[1],color='green',marker='x')
			for pts in self.v[1::]:
				ax.scatter(pts[0],pts[1],color='red',marker='o')
			for pts in self.plane_pts:
				ax.scatter(pts[0],pts[1],color='red',marker='.')
			for pts in self.boundary:
				ax.scatter(pts[0],pts[1],color='blue',marker='.')
		if self.dim == 3:
			color = "blue"
			# ax.scatter(self.anti_y[0], self.anti_y[1], self.anti_y[2], color="blue",marker='*')
			# for pts in self.v[1::]:
			# 	ax.scatter(pts[0], pts[1], pts[2], color="green",marker='o')
			# for pts in self.plane_pts:
			# 	ax.scatter(pts[0], pts[1], pts[2], color="black",marker='.')
			for pts in self.boundary:
				ax.scatter(pts[0], pts[1], pts[2], color=color,marker='.')


	def _distance(self, pt1, pt2=None):
		if pt2 is None:
			pt2 = [0] * len(pt1)
		return math.sqrt(sum((np.array(pt1) - np.array(pt2))**2))


class RNBI_linear(RNBI):
	def __init__(self, params):
		self.optimizer = mosek_linear.mosek_linearp
		RNBI.__init__(self, params)

class RNBI_quadratic(RNBI):
	def __init__(self, params):
		self.optimizer = mosek_quadratic.mosek_quadraticp
		RNBI.__init__(self, params)


	




if __name__ == '__main__':
	M = 9
	params = {
			  # "map matrix from variable space to objective space"
	          "Y"  : [[1, 0], [0, 1]],
	          # "min y1" 
	          # "min y2" 
	          "direction": [1, 1],
	          # "feasible region define"
	          "A_con"  : [[-1, 0], [0, -1], [M, 1], [0, 1]], 
	          "Q_con" : None,
	          "blc"  : [-M-1, -M-1, M*M+1, 1], 
	          "buc"  : [mosek_g.INF, mosek_g.INF, mosek_g.INF, mosek_g.INF], 
	          "blx"  : [-mosek_g.INF, -mosek_g.INF], 
	          "bux"  : [mosek_g.INF, mosek_g.INF], 
	          "step_size": 0.5,
	          # "projection_points": 50,
	        }
	ax = plt.subplot(111)
	# RNBI_linear for linear constraints 
	# RNBI_quadratic for quadratic constraints
	rnbi = RNBI_linear(params)
	result = rnbi.solve()
	rnbi.visual(ax)
	plt.show()