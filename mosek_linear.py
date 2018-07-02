import sys
import mosek
import mosek_g



class mosek_linearp(object):

    def __init__(self, params):
        params = mosek_g.params_init(params)
        self._INF = mosek_g.INF
        self.C_obj = params['C_obj']
        self.buc = params['buc']
        self.blc = params['blc']
        self.bux = params['bux']
        self.blx = params['blx']
        self.A_con = list(map(list, zip(*params['A_con'])))
        self.minimize = params['minimize']
        self.silent = params.get('silent', True)
        self.bkc = []
        self.bkx = []
        self.asub = []
        self.aval = []
        self.numcon = len(self.buc)
        self.numvar = len(self.bux)
        self.result = {"x": None, "obj": None, "msg": "Do not finished.", "code":-1}

    def streamprinter(self, text):
        sys.stdout.write(text)
        sys.stdout.flush()

    def fit(self):
        with mosek.Env() as env:
            with env.Task(0, 0) as task:
                if self.silent is False:
                    task.set_Stream(mosek.streamtype.log, self.streamprinter)
                for i, j in zip(self.blc, self.buc):
                    if i <= -self._INF and j>= self._INF:
                        self.bkc.append(mosek.boundkey.fr)
                    elif i > -self._INF and j>= self._INF:
                        self.bkc.append(mosek.boundkey.lo)
                    elif i > -self._INF and j < self._INF:
                        self.bkc.append(mosek.boundkey.ra)
                    elif i <= -self._INF and j < self._INF:
                        self.bkc.append(mosek.boundkey.up)
                    elif i == j and i > -self._INF and j < self._INF:
                        self.bkc.append(mosek.boundkey.fx)
                for i, j in zip(self.blx, self.bux):
                    if i <= -self._INF and j>= self._INF:
                        self.bkx.append(mosek.boundkey.fr)
                    elif i > -self._INF and j>= self._INF:
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
                    task.putvarbound(i, self.bkx[i], self.blx[i], self.bux[i])
                    # Input column i of A
                    task.putacol(i, self.asub[i], self.aval[i])

                # Set the bounds on constraints.
                # blc[i] <= constraint_i <= buc[i]
                for i in range(self.numcon):
                    task.putconbound(i, self.bkc[i], self.blc[i], self.buc[i])

                # Input the objective sense (minimize/maximize)
                if self.minimize is True:
                    task.putobjsense(mosek.objsense.minimize)
                else:
                    task.putobjsense(mosek.objsense.maximize)
                # Solve the problem
                task.optimize()

                task.solutionsummary(mosek.streamtype.msg)
                solsta = task.getsolsta(mosek.soltype.bas)

                if (solsta == mosek.solsta.optimal or solsta == mosek.solsta.near_optimal):
                    self.result["x"] = [0.] * self.numvar
                    task.getxx(mosek.soltype.bas, self.result["x"])
                    self.result["obj"] = task.getprimalobj(mosek.soltype.bas)
                    self.result["code"] = 0
                    self.result["msg"] = "Optimal solution"
                elif (solsta == mosek.solsta.dual_infeas_cer or \
                      solsta == mosek.solsta.prim_infeas_cer or \
                      solsta == mosek.solsta.near_dual_infeas_cer or \
                      solsta == mosek.solsta.near_prim_infeas_cer):
                    self.result["msg"] = "Primal or dual infeasibility certificate found."
                elif solsta == mosek.solsta.unknown:
                    self.result["msg"] = "Unknown solution status"
                else:
                    self.result["msg"] = "Other solution status"
                print(self.result["msg"])
                return self.result["code"], self.result


def main():

    ans = "[0.0, 0.0, 15.0, 8.333333333333334]"

    params = {"C_obj"  : [3, 1, 5, 1], 
              "A_con"  : [[3, 1, 2, 0], [2, 1, 3, 1], [0, 2, 0, 3]], 
              "blc"  : [30, 15, -mosek_g.INF], 
              "buc"  : [30, mosek_g.INF, 25], 
              "blx"  : [0, 0, 0, 0], 
              "bux"  : [mosek_g.INF, 10, mosek_g.INF, mosek_g.INF], 
              "minimize" :False, 
              "silent": False
            }
    pro = mosek_linearp(params)

    code, result = pro.fit()

    if code == 0:
        print(result)

if __name__ == '__main__':
    main()