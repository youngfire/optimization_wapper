# Mosek wrapper

---
## 线性规划

Src:

mosek_linear.py

Problem:

$$
\max 3x_0+1x_1+5x_2+1x_3 \\
\text{s.t. } 3x_0+1x_1+2x_2=30\\
2x_0+1x_1+3x_2+1x_3\geq 15 \\
2x_1+3x_3\leq25 \\
0\leq x_0\leq \infty \\
0\leq x_1\leq 10 \\
0\leq x_2\leq \infty \\
0\leq x_3\leq \infty
$$

Ans:

$$
x=[0.0, 0.0, 15.0, 8.333333333333334]
$$

## 混合整数线性规划

Src:

mosek_integer.py

Problem:

$$
\max 7x_0+10x_1+1x_2+5x_3 \\
\text{s.t. } x_0+x_1+x_2+x_3\leq 2.5\\
x_0,x_1,x_2\in \mathbb{Z} \\
x_0,x_1,x_2,x_3\geq 0
$$

Ans:

$$
x=[0.0, 2.0, 0.0, 0.5]
$$

## 二次优化

Src:

mosek_quadratic.py

Problem:

$$
\min \frac{1}{2}x^TQ^{obj}x+c^Tx \\
\text{s.t. }\frac{1}{2}x^TQ^{con0}x+Ax\geq b,\\
x\geq 0
$$

where

$$
Q^{obj}=\left[
 \begin{matrix}
   2 & 0 & -1 \\
   0 & 0.2 & 0 \\
   -1 & 0 & 2
  \end{matrix}
  \right], c=[0, -1, 0]^T, A=[1,1,1],b=1\\
Q^{con0}=\left[
 \begin{matrix}
   -2 & 0 & 0.2 \\
   0 & -2 & 0 \\
   0.2 & 0 & -0.2
  \end{matrix}
  \right]
$$

Ans: 

$$
x=[0.4488485199618974, 0.9319361480448437, 0.6741131920778094]
$$


