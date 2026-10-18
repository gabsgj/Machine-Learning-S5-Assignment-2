# Deliverable 1 — Formal Embedding Design

## 1. Formal application model

The application is represented as

\[
A=(S,C,S_I,G,R,K)
\]

where \(S\) is the state space, \(C\) is the capability set, \(S_I\) is the
initial state, \(G\) is the goal specification, \(R\) is the resource set and
\(K\) is the set of global constraints.

A state is

\[
S=\{(x_1,v_1),\ldots,(x_n,v_n)\}.
\]

A goal is a set of desired assignments

\[
G=\{g_1,\ldots,g_m\}.
\]

## 2. Capability representation

Each capability is represented as

\[
C_i=(T_i,I_i,O_i,P_i,E_i,K_i,R_i,Q_i,Rel_i,A_i,M_i).
\]

- \(T_i\): capability type
- \(I_i,O_i\): input/output specifications
- \(P_i,E_i\): preconditions/effects
- \(K_i\): capability constraints
- \(R_i\): resources
- \(Q_i\): operational costs
- \(Rel_i\): reliability
- \(A_i\): availability
- \(M_i\): execution mechanism

The implementation keeps these fields explicitly in JSON; the embedding is
constructed from their structured features.

## 3. Structured vector embedding

Let \(V\) be a vocabulary of formal tokens obtained from all supplied
application problems. Tokens include:

- `TYPE:t`
- `PRE:x=v`
- `EFF:x=v`
- `IN_TYPE:t`
- `OUT_TYPE:t`
- `CON:k`
- `RES:r`
- `MECH:k=v`

The semantic portion of a capability vector is a weighted multi-hot vector:

\[
z_i =
2z_T+2z_P+2.5z_E+1.2z_{I,type}+1.4z_{O,type}
+0.7z_{I,name}+0.8z_{O,name}+0.8z_K+0.8z_R+0.4z_M.
\]

The operational block is

\[
q_i=(\log(1+t_i)/\log(10001),r_i,m_i,\rho_i,e_i,Rel_i,A_i)
\]

where \(t\) is time, \(r\) resource cost, \(m\) monetary cost,
\(\rho\) risk and \(e\) energy.

The final vector is

\[
\phi_C(C_i)=Normalize([z_i,q_i]).
\]

This is a problem-specific embedding rather than direct use of a pretrained
language model.

## 4. State and goal embeddings

State and goal conditions use the same state-variable vocabulary:

\[
\phi_S(S)=Normalize(\sum_{(x,v)\in S}e_{x=v})
\]

\[
\phi_G(G)=Normalize(\sum_{(x,v)\in G}e_{x=v}).
\]

This gives a common coordinate system for state/goal conditions and allows
capability effects to be compared with desired goal conditions.

## 5. Compatibility

For \(C_i\rightarrow C_j\), define

\[
M_P=\frac{|\{p\in P_j:E_i\models p\}|}{|P_j|}
\]

and

\[
M_{IO}=
\begin{cases}
1 & O_i\cap I_j\neq\emptyset\\
0 & otherwise.
\end{cases}
\]

Let \(M_R\) be the fraction of \(C_j\)'s resources also available to \(C_i\).

The reported compatibility score is

\[
Comp(C_i,C_j)=0.7M_P+0.2M_{IO}+0.1M_R.
\]

A pair is declared composable when all required preconditions are satisfied
and an input/output dependency is available when an input is required.

This distinction is intentional: cosine similarity measures resemblance,
whereas compatibility checks executable dependency.

## 6. Composition

For a valid sequence

\[
C_1:S_0\rightarrow S_1,\ldots,C_n:S_{n-1}\rightarrow S_n
\]

the composite capability is

\[
C_{1:n}=C_n\circ\cdots\circ C_1.
\]

Its vector is a weighted normalized aggregation:

\[
\phi(C_{1:n})=
Normalize\left(\sum_{i=1}^{n}(1+0.05(i-1))\,\phi_{raw}(C_i)\right)
\]

with the operational block replaced by aggregate values:

\[
t_{tot}=\sum t_i,\quad
r_{tot}=\sum r_i,\quad
m_{tot}=\sum m_i,
\]

\[
\rho_{tot}=\frac{1}{n}\sum\rho_i,\quad
e_{tot}=\sum e_i,
\]

\[
Rel_{tot}=\prod Rel_i,\qquad
A_{tot}=\min A_i.
\]

The small positional weight prevents a pure unordered average while retaining
a fixed-size representation.

## 7. Similarity

For encoded vectors \(x,y\),

\[
sim(x,y)=\frac{x^Ty}{||x||||y||}.
\]

Cosine similarity is used for functional resemblance. It is never treated as a
replacement for formal precondition/effect compatibility.
