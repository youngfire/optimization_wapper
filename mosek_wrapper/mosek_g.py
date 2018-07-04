INF = 10000000000
EPS = 0.000000001


def params_init(params):
	C_obj = params.get('C_obj', None)
	C_obj = [] if not C_obj else C_obj
	params["C_obj"] = C_obj
	Q_obj = params.get('Q_obj', None)
	Q_obj = [] if not Q_obj else Q_obj
	params["Q_obj"] = Q_obj
	A_con = params.get('A_con', None)
	A_con = [] if not A_con else A_con
	params["A_con"] = A_con
	Q_con = params.get('Q_con', None)
	params["Q_con"] = [] if not Q_con else Q_con
	buc = params.get('buc', None)
	params["buc"] = [] if not buc else buc
	blc = params.get('blc', None)
	params["blc"] = [] if not blc else blc
	bux = params.get('bux', None)
	params["bux"] = [] if not bux else bux
	blx = params.get('blx', None)
	params["blx"] = [] if not blx else blx
	return params