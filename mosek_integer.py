import sys
import mosek
import mosek_g
# Since the actual value of Infinity is ignores, we define it solely
# for symbolic purposes:



class mosek_integerp(object):
    def __init__(self, params):
        self._INF = mosek_g.INF
        self.C_obj = params['C_obj']
        self.A_con = list(map(list, zip(*params['A_con'])))
        self.buc = params['buc']
        self.blc = params['blc']
        self.bux = params['bux']
        self.blx = params['blx']
        self.initial = params.get('initial', None)
        self.minimize = params.get('minimize', True)
        self.integ_flag = params.get('integ_flag', [])
        self.silent = params.get('silent', True)
        self.bkc = []
        self.bkx = []
        self.asub = []
        self.aval = []
        self.numcon = len(self.buc)
        self.numvar = len(self.bux)
        self.max_time = params.get('max_time', 60)
        self.result = {"x": None, "obj": None, "msg": "Do not finished.", "code":-1}

    def streamprinter(self, text):
        sys.stdout.write(text)
        sys.stdout.flush()

    def fit(self, ):
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

                for i in range(self.numcon):
                    task.putconbound(i, self.bkc[i], self.blc[i], self.buc[i])

                if self.minimize is True:
                    task.putobjsense(mosek.objsense.minimize)
                else:
                    task.putobjsense(mosek.objsense.maximize)

                # Define variables to be integers
                # A list of variable indexes for which the variable type should be changed
                if sum(self.integ_flag)>0:
                    integ_index = []
                    for i, flag in enumerate(self.integ_flag, start=0):
                        if flag > 0:
                            integ_index.append(i)
                    task.putvartypelist(integ_index, [mosek.variabletype.type_int] * len(integ_index))
                if self.initial:
                    # Construct an initial feasible solution from the
                    # values of the integer valuse specified
                    task.putintparam(mosek.iparam.mio_construct_sol, mosek.onoffkey.on)
                    # Assign values 0,2,0 to integer variables. Important to
                    # assign a value to all integer constrained variables.
                    task.putxxslice(mosek.soltype.itg, 0, len(self.initial), self.initial)
                # Set max solution time 
                task.putdouparam(mosek.dparam.mio_max_time, self.max_time);

                task.optimize()

                task.solutionsummary(mosek.streamtype.msg)
                prosta = task.getprosta(mosek.soltype.itg)
                solsta = task.getsolsta(mosek.soltype.itg)

                if solsta in [mosek.solsta.integer_optimal, mosek.solsta.near_integer_optimal]:
                    self.result["x"] = [0.] * self.numvar
                    task.getxx(mosek.soltype.itg, self.result["x"])
                    self.result["obj"] = task.getprimalobj(mosek.soltype.itg)
                    self.result["code"] = 0
                    self.result["msg"] = "Optimal solution"
                elif solsta == mosek.solsta.dual_infeas_cer:
                    self.result["msg"] = "Primal or dual infeasibility."
                elif solsta == mosek.solsta.prim_infeas_cer:
                    self.result["msg"] = "Primal or dual infeasibility."
                elif solsta == mosek.solsta.near_dual_infeas_cer:
                    self.result["msg"] = "Primal or dual infeasibility."
                elif solsta == mosek.solsta.near_prim_infeas_cer:
                    self.result["msg"] = "Primal or dual infeasibility."
                elif mosek.solsta.unknown:
                    if prosta == mosek.prosta.prim_infeas_or_unbounded:
                        self.result["msg"] = "Problem status Infeasible or unbounded."
                    elif prosta == mosek.prosta.prim_infeas:
                        self.result["msg"] = "Problem status Infeasible."
                    elif prosta == mosek.prosta.unkown:
                        self.result["msg"] = "Problem status unkown."
                    else:
                        self.result["msg"] = "Other problem status."
                else:
                    self.result["msg"] = "Other solution sta."
                print(self.result["msg"])
                return self.result["code"], self.result


def main():
    ans = "[0.0, 2.0, 0.0, 0.5]"
    params = {"C_obj"  : [7, 10, 1, 5], 
              "A_con"  : [[1, 1, 1, 1]], 
              "blc"  : [-mosek_g.INF], 
              "buc"  : [2.5], 
              "blx"  : [0, 0, 0, 0], 
              "bux"  : [mosek_g.INF, mosek_g.INF, mosek_g.INF, mosek_g.INF],
              "minimize" :False,
              "integ_flag" :[1, 1, 1, 0],
              "silent": True,
            }
    pro = mosek_integerp(params)
    code, result = pro.fit()
    if code == 0:
        print(result)


if __name__ == '__main__':
    main()
    
