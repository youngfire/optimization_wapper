import sys
import mosek
import mosek_g
# Since the actual value of Infinity is ignores, we define it solely
# for symbolic purposes:


class mosek_quadraticp(object):

	def __init__(self, params):
	    self._INF = mosek_g.INF
	    self.C_obj = params['C_obj']
	    self.Q_obj = params['Q_obj']
	    self.A_con = list(map(list, zip(*params['A_con'])))
	    self.Q_con = params['Q_con']
	    self.buc = params['buc']
	    self.blc = params['blc']
	    self.bux = params['bux']
	    self.blx = params['blx']
	    self.initial = params.get('initial', None)
	    self.minimize = params.get('minimize', True)
	    self.integ_index = params.get('integ_index', [])
	    self.silent = params.get('silent', True)
	    self.bkc = []
	    self.bkx = []
	    self.asub = []
	    self.aval = []
	    self.numcon = len(self.buc)
	    self.numvar = len(self.bux)
	    self.xx = None
	    self.opti = None
	    self.max_time = params.get('max_time', 60)
	    self.qsubi = []
	    self.qsubj = []
	    self.qval = []

	def streamprinter(self, text):
	    sys.stdout.write(text)
	    sys.stdout.flush()

	def fit(self, ):
		with mosek.Env() as env:
			with env.Task(0, 0) as task:
				if self.silent is False:
					task.set_Stream(mosek.streamtype.log, self.streamprinter)
				for i, j in zip(self.blc, self.buc):
					if i <= -self._INF and j >= self._INF:
						self.bkc.append(mosek.boundkey.fr)
					elif i > -self._INF and j >= self._INF:
						self.bkc.append(mosek.boundkey.lo)
					elif i > -self._INF and j < self._INF:
						self.bkc.append(mosek.boundkey.ra)
					elif i <= -self._INF and j < self._INF:
						self.bkc.append(mosek.boundkey.up)
					elif i == j and i > -self._INF and j < self._INF:
						self.bkc.append(mosek.boundkey.fx)
				for i, j in zip(self.blx, self.bux):
					if i <= -self._INF and j >= self._INF:
						self.bkx.append(mosek.boundkey.fr)
					elif i > -self._INF and j >= self._INF:
						self.bkx.append(mosek.boundkey.lo)
					elif i > -self._INF and j < self._INF:
						self.bkx.append(mosek.boundkey.ra)
					elif i <= -self._INF and j < self._INF:
						self.bkx.append(mosek.boundkey.up)
					elif i == j and i > -self._INF and j < self._INF:
						self.bkx.append(mosek.boundkey.fx)

				for A_vec in self.A_con:
					asub_tmp = []
					aval_tmp = []
					for i, elm in enumerate(A_vec):
						if elm != 0:
							asub_tmp.append(i)
							aval_tmp.append(float(elm))
					self.asub.append(asub_tmp)
					self.aval.append(aval_tmp)

				task.appendcons(self.numcon)
				task.appendvars(self.numvar)

				for i in range(self.numvar):
					# Set the linear term c_i in the objective.
					task.putcj(i, self.C_obj[i])

					# Set the bounds on variable i
					# blx[i] <= x_i <= bux[i]
					task.putbound(mosek.accmode.var, i, self.bkx[i], self.blx[i], self.bux[i])
					# Input column i of A
					task.putacol(i, self.asub[i], self.aval[i])

				for i in range(self.numcon):
				    task.putbound(mosek.accmode.con, i, self.bkc[i], self.blc[i], self.buc[i])

				# Set up and input quadratic objective
				self.qsubi = []
				self.qsubj = []
				self.qval = []
				for i in range(0, self.numvar):
					for j in range(0, i + 1):
						if abs(self.Q_obj[i][j]) >= 0.000001:
							self.qsubi.append(i)
							self.qsubj.append(j)
							self.qval.append(self.Q_obj[i][j])
				task.putqobj(self.qsubi, self.qsubj, self.qval)

				for k in range(0, self.numcon):
					Q_con_k = self.Q_con[k]
					self.qsubi = []
					self.qsubj = []
					self.qval = []
					for i in range(0, self.numvar):
						for j in range(0, i + 1):
							if abs(Q_con_k[i][j]) >= 0.000001:
								self.qsubi.append(i)
								self.qsubj.append(j)
								self.qval.append(Q_con_k[i][j])
					task.putqconk(k, self.qsubi, self.qsubj, self.qval)


				if self.minimize is True:
				    task.putobjsense(mosek.objsense.minimize)
				else:
				    task.putobjsense(mosek.objsense.maximize)


				task.optimize()
				task.solutionsummary(mosek.streamtype.msg)
				prosta = task.getprosta(mosek.soltype.itr)
				solsta = task.getsolsta(mosek.soltype.itr)

				self.xx = [0.] * self.numvar
				task.getxx(mosek.soltype.itr, self.xx)
				result = "Do not finished."
				if solsta == mosek.solsta.optimal or solsta == mosek.solsta.near_optimal:
					result = {"x": self.xx}
					print("Optimal solution")
					return 0, result
				elif solsta == mosek.solsta.dual_infeas_cer:
					result = "Primal or dual infeasibility.\n"
				elif solsta == mosek.solsta.prim_infeas_cer:
					result = "Primal or dual infeasibility.\n"
				elif solsta == mosek.solsta.near_dual_infeas_cer:
					result = "Primal or dual infeasibility.\n"
				elif solsta == mosek.solsta.near_prim_infeas_cer:
					result = "Primal or dual infeasibility.\n"
				elif mosek.solsta.unknown:
					result = "Unknown solution status"
				else:
					result = "Other solution status"
				print(result)
				return -1, result


def main():
	ans = "[0.4488485199618974, 0.9319361480448437, 0.6741131920778094]"


	Q_obj = [[2, 0, -1], [0, 0.2, 0], [-1, 0, 2]]
	Q_con_0 = [[-2, 0, 0.2], [0, -2, 0], [0.2, 0, -0.2]]
	Q_con = [Q_con_0]

	params = {"C_obj"  : [0, -1, 0],
    		  "Q_obj"  : Q_obj,
              "A_con"  : [[1, 1, 1]],
              "Q_con"  : Q_con,
              "blc"  : [1],
              "buc"  : [mosek_g.INF],
              "blx"  : [0, 0, 0],
              "bux"  : [mosek_g.INF, mosek_g.INF, mosek_g.INF],
              "minimize" :True,
              "silent": False
            }
    

	pro = mosek_quadraticp(params)

	code, result = pro.fit()

	if code == 0:
	    print(result["x"])


if __name__ == '__main__':
	main()




