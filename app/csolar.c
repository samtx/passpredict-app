#include "passpredict.h"

/* Compute the Sun position vector

    Inputs:
       jd, double[n]: julian date array
       r, double[n, 3]: position vector to return in-place
       n, int: number of time steps, size of jd

    References:
        Vallado, p. 279, Alg. 29
        Vallado software, AST2BODY.FOR, subroutine SUN
    */
void c_sun_pos(double *jd, double *r, int n){
    
    double t_ut1, t_tdb, lmda_Msun, M_sun, lmda_eclp;
    double r_sun_mag, eps, coslmda, sinlmda, coseps, sineps;

    int i, j;

    for(i=0; i<n; i++){
        t_ut1 = (jd[i] - DJ00) / DJC; // DJ00=2451545.0, DJC=36525.0
        t_tdb = t_ut1;
        lmda_Msun = fmod(280.4606184 + 36000.77005361*t_tdb, 360);
        // M_sun = (357.5291092 + 35999.05034*t_tdb) % 360;
        M_sun = fmod(357.5277233 + 35999.05034*t_tdb, 360);
        lmda_eclp = lmda_Msun + 1.914666471 * sin(M_sun * DD2R);
        lmda_eclp += 0.019994643 * sin(2 * M_sun * DD2R);
        r_sun_mag = 1.000140612 - 0.016708617 * cos(M_sun * DD2R);
        r_sun_mag -= 0.000139589 * cos(2 * M_sun * DD2R) * (DAU/1000);
        eps = 23.439291 - 0.0130042 * t_tdb;
        coslmda = cos(lmda_eclp * DD2R);
        sinlmda = sin(lmda_eclp * DD2R);
        coseps = cos(eps * DD2R);
        sineps = sin(eps * DD2R);
        r[i*3] = r_sun_mag * coslmda;
        r[i*3 + 1] = r_sun_mag * coseps * sinlmda;
        r[i*3 + 2] = r_sun_mag * sineps * sinlmda;
    }
}


/* Compute the Sun position vector in ECEF coordinates

    Inputs:
       jd, double[n]: julian date array
       r, double[n, 3]: position vector to return in-place
       n, int: number of time steps, size of jd

    References:
        Vallado, p. 279, Alg. 29
        Vallado software, AST2BODY.FOR, subroutine SUN
    */
void c_sun_pos_ecef(double *jd, double *r, int n){

    c_sun_pos(jd, r, n);
    c_mod2ecef(jd, r, n);

    // for(i=0; i<n; i++){
    //     *jd_i = jd[i];
    //     for(j=0; j<3; j++) 
    //         p[j] = r[i*3 + j];
    //     sun_pos(jd_i, p, 1);
    //     sun_mod2itrf(jd_i, p, 1);
    //     for(j=0; j<3; j++)
    //         r[i*3 + j] = p[j];
    // }
}