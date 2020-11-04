#ifndef PASSPREDICT_H
#define PASSPREDICT_H

#include "sofa.h"

/*  crotations.c  */
void c_mod2ecef(double *jd, double *r, int n);
void c_teme2ecef(double *jd, double *r, int n);

/*  csolar.c  */
void c_sun_pos_ecef(double *jd, double *r, int n);
void c_sun_pos(double *jd, double *r, int n);

#endif