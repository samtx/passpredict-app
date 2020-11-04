#include "crotations.h"

/*
Rotate MOD position vector r[n, 3] using 1980 Nutation theory and
1976/FK5 sidereal time 

Rotates in-place

Rotates MOD -> ITRF (ECEF)
*/
void sun_mod2itrf(double *jd, double *r, int n){
    int i, j;

    double dp80, de80, dpsi, deps, epsa, rn[3][3], ee, gst;

    // UTC1 correction set to zero
    // const double dut1 = 0.0;

    // EOP corrections set to zero
    // const double xp = 0.0, yp = 0.0;
    const double ddp80 = 0.0, dde80 = 0.0;

    // Set partial jd to zero
    const double tt = 0.0;
    const double tut = 0.0;

    // temporary position vector
    double p[3] = {0, 0, 0};
    double rnp[3] = {0, 0, 0};

    for(i=0; i<n; i++){

        /* IAU 1980 Nutation */
        iauNut80(jd[i], tt, &dp80, &de80); 
        dpsi = dp80 + ddp80;
        deps = de80 + dde80;
        /* Mean obliquity. */
        epsa = iauObl80(jd[i], tt);
        /* Build the rotation matrix. */
        iauNumat(epsa, dpsi, deps, rn);
        /* Equation of the equinoxes, including nutation correction. */
        ee = iauEqeq94(jd[i], tt) + ddp80 * cos(epsa);
        /* Greenwich apparent sidereal time (IAU 1982/1994). */
        gst = iauAnp(iauGmst82(jd[i], tut) + ee);
        /* Form celestial-terrestrial matrix (no polar motion yet). */
        iauRz(gst, rn);

        /* Rotate the i position vector in-place */
        for(j=0; j<3; j++) 
            p[j] = r[i*3 + j];
        iauRxp(rn, p, rnp);
        for(j=0; j<3; j++) 
            r[i*3 + j] = rnp[j];   
    }
}