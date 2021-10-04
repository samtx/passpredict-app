# Astrodynamics

## Coordinate Frame Rotation

Converting TEME position vectors to ECEF position vectors.

The ECEF coordinate frame can be approximated with the PEF coordinate frame. (p.233)

$$
\mathbf{r}_{PEF} = \mathrm{ROT}3(\theta_{\mathrm{GMST}})\mathbf{r}_{TEME}
$$

$$
\mathrm{ROT}3(\theta_{\mathrm{GMST}}) =
\begin{pmatrix}
\cos\theta & -\sin\theta & 0 \\
\sin\theta & \cos\theta & 0 \\
0   &   0   &  1
\end{pmatrix}
$$


$$
\begin{bmatrix}
R_x \\
R_y \\
R_z
\end{bmatrix}_{\mathrm{PEF}}
=
\begin{pmatrix}
\cos\theta & -\sin\theta & 0 \\
\sin\theta & \cos\theta & 0 \\
0   &   0   &  1
\end{pmatrix}
\begin{bmatrix}
R_x \\
R_y \\
R_z
\end{bmatrix}_{\mathrm{TEME}}
$$


\begin{align}
R_{x,\mathrm{PEF}} &= \cos\theta \cdot R_{x,\mathrm{TEME}} - \sin\theta \cdot R_{y,\mathrm{TEME}}\\
R_{y,\mathrm{PEF}} &= \\
R_{z,\mathrm{PEF}} &=
\end{align}


Greenwich mean sidereal time, 1982 model

\begin{gather}
\theta_{\mathrm{GMST}} = 67310.45841^\mathrm{s} + (876600^{\mathrm{h}} + 8640184.812886^{\mathrm{s}}) \; T_{\mathrm{UT1}} \\ + \; 0.093104 \; T_{\mathrm{UT1}}^2 - 6.2 \times 10^{-6} \; T_{\mathrm{UT1}}^3
\end{gather}

Seconds of time to radians, \( DS2R = \frac{radians/day}{seconds/day} \)

\begin{aligned}
    DS2R &= \frac{2\pi}{86400} \\
    DS2R &= 7.272205216643039903848712 \times 10^{-5}
\end{aligned}

\begin{align}
\theta_{\mathrm{GMST}} &=  \\
A &= 24110.54841 - 86400 / 2 \\
B &= 8640184.812866 \\
C &= 0.093104 \\
D &= -6.2 \times 10^{-6}
\end{align}

\theta_{\mathrm{GMST}} = DS2R

Terrestial time

\begin{align}
UTC &= UT1 - \Delta UT1 \\
TAI &= UTC + \Delta AT \\
TT &= TAI + 32.184^s
\end{align}