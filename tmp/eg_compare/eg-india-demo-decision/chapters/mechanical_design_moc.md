## Mechanical Design and MoC

| Equipment | Type | Shell t (mm) | Head t (mm) | Class | Hydrotest (bar) | Nozzle (mm) | Support | Load Case | Support t (mm) | Load (kN) | Thermal Growth (mm) | Reinforcement (mm2) | Platform |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-101 | Reactor | 157.13 | 144.56 | ASME 600 | 26.00 | 9336.1 | skirt support | operating + wind + seismic + nozzle loads | 109.99 | 259711.84 | 148.17 | 1941902.0 | yes |
| PU-201 | Distillation column | 4.41 | 4.06 | PN16 | 3.00 | 640.2 | skirt support | operating + wind + seismic + nozzle loads | 24.00 | 250.03 | 6.83 | 13316.9 | yes |
| V-101 | Flash drum | 15.94 | 14.66 | PN16 | 4.00 | 3917.0 | base support | operating + nozzle loads | 24.00 | 46738.28 | 21.82 | 65806.4 | no |
| E-101 | Heat exchanger | 21.34 | 19.63 | ASME 150 | 10.40 | 2021.0 | saddle support | operating + nozzle loads | 24.00 | 7376.03 | 29.89 | 90539.7 | yes |
| TK-301 | Storage tank | 9.19 | 8.45 | PN16 | 2.20 | 5177.3 | saddle / leg support | operating + settlement + thermal growth | 18.00 | 75768.79 | 12.46 | 34791.6 | no |
| HX-01 | HTM loop exchanger | 25.95 | 23.87 | ASME 300 | 14.30 | 1822.7 | saddle support | operating + nozzle loads | 24.00 | 5636.10 | 32.93 | 152379.0 | yes |
| HX-01-CTRL | Utility control package | 0.00 | 0.00 | ASME 150 | 11.70 | 25.0 | instrument frame | skid dead load + piping reaction | 12.00 | 6.00 | 5.77 | 1260.0 | no |
| HX-01-HDR | Shared HTM header manifold | 8.60 | 7.92 | ASME 300 | 18.85 | 417.0 | pipe rack support | rack piping + thermal expansion | 24.00 | 594.50 | 5.83 | 45956.1 | no |
| HX-01-PMP | HTM circulation skid | 8.60 | 7.92 | ASME 300 | 18.85 | 117.3 | base frame | operating + nozzle loads | 24.00 | 10.59 | 5.83 | 12930.0 | no |
| HX-01-EXP | HTM expansion tank | 5.31 | 4.88 | ASME 150 | 7.80 | 175.1 | leg support | operating + settlement + thermal growth | 18.00 | 33.03 | 5.99 | 7984.8 | no |
| HX-01-RV | HTM relief package | 8.21 | 7.56 | ASME 300 | 17.55 | 145.4 | base support | operating + nozzle loads | 24.00 | 18.91 | 6.09 | 14920.7 | no |
| HX-02 | Heat integration exchanger | 8.95 | 8.24 | ASME 150 | 8.45 | 613.7 | saddle support | operating + nozzle loads | 24.00 | 402.13 | 13.00 | 22339.3 | yes |
| HX-02-CTRL | Utility control package | 0.00 | 0.00 | ASME 150 | 6.50 | 25.0 | instrument frame | skid dead load + piping reaction | 12.00 | 6.00 | 4.31 | 700.0 | no |

### Mechanical Basis

| Field | Value |
| --- | --- |
| Code basis | ASME-style screening logic |
| Design pressure basis | Selected equipment design pressure with feasibility-study margin |
| Design temperature basis | Selected equipment design temperature with preliminary utility envelope |
| Support design basis | Support screening includes vertical, piping, wind, seismic, and thermal-growth load components by equipment family. |
| Load case basis | Tall process equipment uses operating + wind + seismic + nozzle loads; headers use rack piping + thermal expansion; skids use dead load + piping reaction. |
| Foundation basis | Support variants differentiate skirt, saddle, leg, rack, and skid foundations with screening footprint and anchor-group logic. |
| Nozzle load basis | Nozzle schedules include reinforcement family, local shell interaction, orientation, projection, and screening piping load allocation. |
| Connection rating basis | Nozzle and header connection classes follow design-pressure screening via ASME/PN envelope mapping. |
| Access platform basis | Columns, absorbers, reactors, and exchanger services above grade include screening access-platform area allowances. |

### Mechanical Design Input Matrix

| Equipment | Type | Pdesign (bar) | Tdesign (C) | Allowable Stress (MPa) | Joint Efficiency | CA (mm) | Pressure Class |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R-101 | Reactor | 20.00 | 255.0 | 138.0 | 0.85 | 3.00 | ASME 600 |
| PU-201 | Distillation column | 2.00 | 140.0 | 138.0 | 0.85 | 3.00 | PN16 |
| V-101 | Flash drum | 3.00 | 85.0 | 138.0 | 0.85 | 3.00 | PN16 |
| E-101 | Heat exchanger | 8.00 | 180.0 | 138.0 | 0.85 | 3.00 | ASME 150 |
| TK-301 | Storage tank | 1.20 | 45.0 | 120.0 | 0.85 | 2.00 | PN16 |
| HX-01 | HTM loop exchanger | 11.00 | 213.0 | 138.0 | 0.85 | 3.00 | ASME 300 |
| HX-01-CTRL | Utility control package | 9.00 | 203.0 | 138.0 | 0.85 | 3.00 | ASME 150 |
| HX-01-HDR | Shared HTM header manifold | 14.50 | 205.0 | 138.0 | 0.85 | 3.00 | ASME 300 |
| HX-01-PMP | HTM circulation skid | 14.50 | 205.0 | 138.0 | 0.85 | 3.00 | ASME 300 |
| HX-01-EXP | HTM expansion tank | 6.00 | 210.0 | 138.0 | 0.85 | 3.00 | ASME 150 |
| HX-01-RV | HTM relief package | 13.50 | 213.0 | 138.0 | 0.85 | 3.00 | ASME 300 |
| HX-02 | Heat integration exchanger | 6.50 | 162.0 | 120.0 | 0.85 | 3.00 | ASME 150 |
| HX-02-CTRL | Utility control package | 5.00 | 158.0 | 138.0 | 0.85 | 3.00 | ASME 150 |

| Equipment | Load Case | Support Load (kN) | Wind (kN) | Seismic (kN) | Piping (kN) | Anchor Bolt (mm) | Base Plate (mm) | Platform | Platform Area (m2) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-101 | operating + wind + seismic + nozzle loads | 328630.148 | 1152.822 | 46748.132 | 240.402 | 10269.688 | 185.721 | yes | 61.737 |
| PU-201 | operating + wind + seismic + nozzle loads | 341.554 | 9.813 | 45.005 | 16.706 | 149.391 | 21.185 | yes | 5.696 |
| V-101 | operating + nozzle loads | 55418.590 | 168.445 | 4673.828 | 98.976 | 2247.216 | 33.876 | no | 0.000 |
| E-101 | operating + nozzle loads | 8804.373 | 47.328 | 737.603 | 53.324 | 664.724 | 24.186 | yes | 3.000 |
| TK-301 | operating + settlement + thermal growth | 89850.174 | 313.146 | 7576.879 | 129.853 | 3385.266 | 40.352 | no | 0.000 |
| HX-01 | operating + nozzle loads | 6761.324 | 39.069 | 563.610 | 71.656 | 570.030 | 23.526 | yes | 3.000 |
| HX-01-CTRL | skid dead load + piping reaction | 45.600 | 1.500 | 1.000 | 3.775 | 20.000 | 18.000 | no | 0.000 |
| HX-01-HDR | rack piping + thermal expansion | 737.938 | 2.066 | 71.340 | 22.476 | 110.194 | 20.565 | no | 0.000 |
| HX-01-PMP | operating + nozzle loads | 91.200 | 1.500 | 1.059 | 11.612 | 28.093 | 20.520 | no | 0.000 |
| HX-01-EXP | operating + settlement + thermal growth | 68.400 | 1.701 | 3.303 | 9.393 | 40.233 | 18.000 | no | 0.000 |
| HX-01-RV | operating + nozzle loads | 91.200 | 1.500 | 1.892 | 12.123 | 34.274 | 20.520 | no | 0.000 |
| HX-02 | operating + nozzle loads | 497.849 | 5.715 | 40.213 | 17.618 | 147.464 | 20.857 | yes | 3.000 |
| HX-02-CTRL | skid dead load + piping reaction | 45.600 | 1.500 | 1.000 | 2.375 | 20.000 | 18.000 | no | 0.000 |

### Foundation and Access Basis

| Equipment | Support Variant | Anchor Groups | Footprint (m2) | Clearance (m) | Ladder | Lifting Lugs |
| --- | --- | --- | --- | --- | --- | --- |
| R-101 | cylindrical skirt with anchor chair | 8 | 656.205 | 1.800 | yes | yes |
| PU-201 | cylindrical skirt with anchor chair | 8 | 6.620 | 1.800 | yes | yes |
| V-101 | grouted base frame | 4 | 12.125 | 1.200 | yes | yes |
| E-101 | dual saddle | 6 | 47.328 | 1.500 | yes | yes |
| TK-301 | dual saddle | 6 | 246.043 | 1.200 | yes | yes |
| HX-01 | dual saddle | 6 | 39.069 | 1.500 | yes | yes |
| HX-01-CTRL | panel frame | 4 | 1.200 | 1.000 | no | no |
| HX-01-HDR | guided rack shoe | 2 | 2.430 | 1.200 | no | yes |
| HX-01-PMP | grouted base frame | 4 | 1.200 | 1.200 | no | no |
| HX-01-EXP | four-leg support | 4 | 1.600 | 1.200 | no | no |
| HX-01-RV | grouted base frame | 4 | 1.200 | 1.200 | no | no |
| HX-02 | dual saddle | 6 | 5.715 | 1.500 | yes | yes |
| HX-02-CTRL | panel frame | 4 | 1.200 | 1.000 | no | no |

### Shell and Head Thickness Derivation

| Equipment | Equation | Substitution | Shell t (mm) | Head t (mm) | CA (mm) | Pressure Class | Hydrotest (bar) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R-101 | t = P*D / (2*S*J - 1.2*P) + CA | P=2.000 MPa; D≈17.895 m; CA=3.0 mm | 157.134 | 144.563 | 3.000 | ASME 600 | 26.000 |
| PU-201 | t = P*D / (2*S*J - 1.2*P) + CA | P=0.200 MPa; D≈1.651 m; CA=3.0 mm | 4.409 | 4.056 | 3.000 | PN16 | 3.000 |
| V-101 | t = P*D / (2*S*J - 1.2*P) + CA | P=0.300 MPa; D≈10.104 m; CA=3.0 mm | 15.940 | 14.665 | 3.000 | PN16 | 4.000 |
| E-101 | t = P*D / (2*S*J - 1.2*P) + CA | P=0.800 MPa; D≈5.356 m; CA=3.0 mm | 21.338 | 19.631 | 3.000 | ASME 150 | 10.400 |
| TK-301 | t = P*D / (2*S*J - 1.2*P) + CA | P=0.120 MPa; D≈12.211 m; CA=2.0 mm | 9.188 | 8.453 | 2.000 | PN16 | 2.200 |
| HX-01 | t = P*D / (2*S*J - 1.2*P) + CA | P=1.100 MPa; D≈4.866 m; CA=3.0 mm | 25.945 | 23.869 | 3.000 | ASME 300 | 14.300 |
| HX-01-HDR | t = P*D / (2*S*J - 1.2*P) + CA | P=1.450 MPa; D≈0.900 m; CA=3.0 mm | 8.604 | 7.916 | 3.000 | ASME 300 | 18.850 |
| HX-01-PMP | t = P*D / (2*S*J - 1.2*P) + CA | P=1.450 MPa; D≈0.900 m; CA=3.0 mm | 8.604 | 7.916 | 3.000 | ASME 300 | 18.850 |
| HX-01-EXP | t = P*D / (2*S*J - 1.2*P) + CA | P=0.600 MPa; D≈0.900 m; CA=3.0 mm | 5.309 | 4.884 | 3.000 | ASME 150 | 7.800 |
| HX-01-RV | t = P*D / (2*S*J - 1.2*P) + CA | P=1.350 MPa; D≈0.900 m; CA=3.0 mm | 8.215 | 7.558 | 3.000 | ASME 300 | 17.550 |
| HX-02 | t = P*D / (2*S*J - 1.2*P) + CA | P=0.650 MPa; D≈1.861 m; CA=3.0 mm | 8.953 | 8.237 | 3.000 | ASME 150 | 8.450 |

### Support and Overturning Derivation

| Equipment | Load Case | Equation | Substitution | Support Load (kN) | Overturning (kN.m) | Anchor Bolt (mm) | Base Plate (mm) | Foundation Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-101 | operating + wind + seismic + nozzle loads | Wsupport = Wvertical + Wpiping + Wwind + Wseismic | Wv=280488.792; Wp=240.402; Ww=1152.822; Ws=46748.132 | 328630.148 | 168812.699 | 10269.688 | 185.721 | Tall vessel service assumes ring foundation and local anchor-chair reinforcement. |
| PU-201 | operating + wind + seismic + nozzle loads | Wsupport = Wvertical + Wpiping + Wwind + Wseismic | Wv=270.030; Wp=16.706; Ww=9.813; Ws=45.005 | 341.554 | 162.518 | 149.391 | 21.185 | Tall vessel service assumes ring foundation and local anchor-chair reinforcement. |
| V-101 | operating + nozzle loads | Wsupport = Wvertical + Wpiping + Wwind + Wseismic | Wv=50477.341; Wp=98.976; Ww=168.445; Ws=4673.828 | 55418.590 | 30379.881 | 2247.216 | 33.876 | Base/foundation detail remains a preliminary screening basis. |
| E-101 | operating + nozzle loads | Wsupport = Wvertical + Wpiping + Wwind + Wseismic | Wv=7966.118; Wp=53.324; Ww=47.328; Ws=737.603 | 8804.373 | 4794.423 | 664.724 | 24.186 | Access platform and ladder loads are included in the support screening basis. |
| TK-301 | operating + settlement + thermal growth | Wsupport = Wvertical + Wpiping + Wwind + Wseismic | Wv=81830.296; Wp=129.853; Ww=313.146; Ws=7576.879 | 89850.174 | 49249.715 | 3385.266 | 40.352 | Base/foundation detail remains a preliminary screening basis. |
| HX-01 | operating + nozzle loads | Wsupport = Wvertical + Wpiping + Wwind + Wseismic | Wv=6086.989; Wp=71.656; Ww=39.069; Ws=563.610 | 6761.324 | 3663.466 | 570.030 | 23.526 | Access platform and ladder loads are included in the support screening basis. |
| HX-01-CTRL | skid dead load + piping reaction | Wsupport = Wvertical + Wpiping + Wwind + Wseismic | Wv=7.000; Wp=3.775; Ww=1.500; Ws=1.000 | 45.600 | 5.000 | 20.000 | 18.000 | Base/foundation detail remains a preliminary screening basis. |
| HX-01-HDR | rack piping + thermal expansion | Wsupport = Wvertical + Wpiping + Wwind + Wseismic | Wv=642.056; Wp=22.476; Ww=2.066; Ws=71.340 | 737.938 | 386.423 | 110.194 | 20.565 | Utility-header service assumes pipe-rack tie-in with local guide/restraint design. |
| HX-01-PMP | operating + nozzle loads | Wsupport = Wvertical + Wpiping + Wwind + Wseismic | Wv=11.589; Wp=11.612; Ww=1.500; Ws=1.059 | 91.200 | 6.883 | 28.093 | 20.520 | Base/foundation detail remains a preliminary screening basis. |
| HX-01-EXP | operating + settlement + thermal growth | Wsupport = Wvertical + Wpiping + Wwind + Wseismic | Wv=35.673; Wp=9.393; Ww=1.701; Ws=3.303 | 68.400 | 21.470 | 40.233 | 18.000 | Base/foundation detail remains a preliminary screening basis. |
| HX-01-RV | operating + nozzle loads | Wsupport = Wvertical + Wpiping + Wwind + Wseismic | Wv=20.428; Wp=12.123; Ww=1.500; Ws=1.892 | 91.200 | 12.295 | 34.274 | 20.520 | Base/foundation detail remains a preliminary screening basis. |
| HX-02 | operating + nozzle loads | Wsupport = Wvertical + Wpiping + Wwind + Wseismic | Wv=434.303; Wp=17.618; Ww=5.715; Ws=40.213 | 497.849 | 261.386 | 147.464 | 20.857 | Access platform and ladder loads are included in the support screening basis. |
| HX-02-CTRL | skid dead load + piping reaction | Wsupport = Wvertical + Wpiping + Wwind + Wseismic | Wv=7.000; Wp=2.375; Ww=1.500; Ws=1.000 | 45.600 | 5.000 | 20.000 | 18.000 | Base/foundation detail remains a preliminary screening basis. |

### Nozzle Reinforcement and Connection Basis

| Equipment | Services | Reinforcement Family | Equation | Substitution | Area (mm2) | Shell Factor | Class | Load Cases (kN) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-101 | feed, product, utility, instrument | integral repad | Areinf = f(dnozzle, Pdesign, equipment family) | d=9336.1 mm; P=20.00 bar | 1941901.983 | 2.359 | ASME 600 | 60.10, 60.10, 60.10, 60.10 |
| PU-201 | feed, overhead, bottoms, instrument | integral repad | Areinf = f(dnozzle, Pdesign, equipment family) | d=640.2 mm; P=2.00 bar | 13316.919 | 1.848 | PN16 | 4.18, 4.18, 4.18, 4.18 |
| V-101 | inlet, outlet, instrument | shell excess area | Areinf = f(dnozzle, Pdesign, equipment family) | d=3917.0 mm; P=3.00 bar | 65806.429 | 1.743 | PN16 | 32.99, 32.99, 32.99 |
| E-101 | inlet, outlet, instrument | shell excess area | Areinf = f(dnozzle, Pdesign, equipment family) | d=2021.0 mm; P=8.00 bar | 90539.654 | 1.799 | ASME 150 | 17.77, 17.77, 17.77 |
| TK-301 | inlet, outlet, vent | shell excess area | Areinf = f(dnozzle, Pdesign, equipment family) | d=5177.3 mm; P=1.20 bar | 34791.617 | 1.781 | PN16 | 43.28, 43.28, 43.28 |
| HX-01 | inlet, outlet, instrument | set-on repad | Areinf = f(dnozzle, Pdesign, equipment family) | d=1822.7 mm; P=11.00 bar | 152378.966 | 1.839 | ASME 300 | 23.89, 23.89, 23.89 |
| HX-01-CTRL | inlet, outlet, instrument | shell excess area | Areinf = f(dnozzle, Pdesign, equipment family) | d=25.0 mm; P=9.00 bar | 1260.000 | 1.185 | ASME 150 | 1.26, 1.26, 1.26 |
| HX-01-HDR | inlet, outlet, branch, drain | set-on repad | Areinf = f(dnozzle, Pdesign, equipment family) | d=417.0 mm; P=14.50 bar | 45956.111 | 2.132 | ASME 300 | 5.62, 5.62, 5.62, 5.62 |
| HX-01-PMP | inlet, outlet, instrument | set-on repad | Areinf = f(dnozzle, Pdesign, equipment family) | d=117.3 mm; P=14.50 bar | 12929.954 | 1.452 | ASME 300 | 3.87, 3.87, 3.87 |
| HX-01-EXP | inlet, outlet, vent | set-on repad | Areinf = f(dnozzle, Pdesign, equipment family) | d=175.1 mm; P=6.00 bar | 7984.835 | 1.440 | ASME 150 | 3.13, 3.13, 3.13 |
| HX-01-RV | inlet, outlet, instrument | set-on repad | Areinf = f(dnozzle, Pdesign, equipment family) | d=145.4 mm; P=13.50 bar | 14920.743 | 1.493 | ASME 300 | 4.04, 4.04, 4.04 |
| HX-02 | inlet, outlet, instrument | shell excess area | Areinf = f(dnozzle, Pdesign, equipment family) | d=613.7 mm; P=6.50 bar | 22339.297 | 1.691 | ASME 150 | 5.87, 5.87, 5.87 |
| HX-02-CTRL | inlet, outlet, instrument | shell excess area | Areinf = f(dnozzle, Pdesign, equipment family) | d=25.0 mm; P=5.00 bar | 700.000 | 1.125 | ASME 150 | 0.80, 0.80, 0.80 |

### Connection and Piping Class Basis

| Equipment | Support Variant | Connection Classes | Piping Class Basis | Orientations (deg) | Projections (mm) | Rack Tie-In |
| --- | --- | --- | --- | --- | --- | --- |
| R-101 | cylindrical skirt with anchor chair | ASME 600, ASME 600, ASME 600, ASME 600 | ASME 600 carbon/alloy steel process class | 0, 90, 180, 270 | 9802.9, 9802.9, 9802.9, 9802.9 | no |
| PU-201 | cylindrical skirt with anchor chair | PN16, PN16, PN16, PN16 | PN16 carbon/alloy steel process class | 0, 90, 180, 270 | 672.2, 672.2, 672.2, 672.2 | no |
| V-101 | grouted base frame | PN16, PN16, PN16 | PN16 carbon/alloy steel process class | 0, 180, 270 | 4112.9, 4112.9, 4112.9 | no |
| E-101 | dual saddle | ASME 150, ASME 150, ASME 150 | ASME 150 thermal-oil / utility piping class | 0, 180, 270 | 2122.0, 2122.0, 2122.0 | no |
| TK-301 | dual saddle | PN16, PN16, PN16 | PN16 tank farm and transfer class | 0, 180, 270 | 5436.2, 5436.2, 5436.2 | no |
| HX-01 | dual saddle | ASME 300, ASME 300, ASME 300 | ASME 300 thermal-oil / utility piping class | 0, 180, 270 | 2278.4, 2278.4, 2278.4 | no |
| HX-01-CTRL | panel frame | ASME 150, ASME 150, ASME 150 | ASME 150 thermal-oil / utility piping class | 0, 180, 270 | 90.0, 90.0, 90.0 | no |
| HX-01-HDR | guided rack shoe | ASME 300, ASME 300, ASME 300, ASME 300 | ASME 300 thermal-oil / utility piping class | 0, 180, 270 | 521.3, 521.3, 521.3, 521.3 | yes |
| HX-01-PMP | grouted base frame | ASME 300, ASME 300, ASME 300 | ASME 300 thermal-oil / utility piping class | 0, 180, 270 | 146.7, 146.7, 146.7 | no |
| HX-01-EXP | four-leg support | ASME 150, ASME 150, ASME 150 | ASME 150 thermal-oil / utility piping class | 0, 180, 270 | 218.9, 218.9, 218.9 | no |
| HX-01-RV | grouted base frame | ASME 300, ASME 300, ASME 300 | ASME 300 thermal-oil / utility piping class | 0, 180, 270 | 181.8, 181.8, 181.8 | no |
| HX-02 | dual saddle | ASME 150, ASME 150, ASME 150 | ASME 150 thermal-oil / utility piping class | 0, 180, 270 | 644.4, 644.4, 644.4 | no |
| HX-02-CTRL | panel frame | ASME 150, ASME 150, ASME 150 | ASME 150 thermal-oil / utility piping class | 0, 180, 270 | 90.0, 90.0, 90.0 | no |

### Material of Construction Matrix

| Equipment | Type | Service | Selected MoC | Design T (C) | Design P (bar) | Service Basis |
| --- | --- | --- | --- | --- | --- | --- |
| R-101 | Reactor | Tubular Plug Flow Hydrator | Carbon Steel | 255.0 | 20.00 | general process service |
| PU-201 | Distillation column | Distillation and purification train | Carbon Steel | 140.0 | 2.00 | general process service |
| V-101 | Flash drum | Intermediate disengagement | Carbon Steel | 85.0 | 3.00 | general process service |
| E-101 | Heat exchanger | R-rough to D-rough heat recovery | Carbon Steel | 180.0 | 8.00 | general process service |
| TK-301 | Storage tank | Ethylene Glycol storage via vertical tank farm | SS304 | 45.0 | 1.20 | general process service |
| HX-01 | HTM loop exchanger | R-rough to D-rough heat recovery | Carbon steel | 213.0 | 11.00 | general process service |
| HX-01-CTRL | Utility control package | R-rough to D-rough heat recovery control valves, instrumentation, and bypass station | Carbon steel | 203.0 | 9.00 | general process service |
| HX-01-HDR | Shared HTM header manifold | R-rough to D-rough heat recovery network header and isolation package | Carbon steel | 205.0 | 14.50 | general process service |
| HX-01-PMP | HTM circulation skid | R-rough to D-rough heat recovery circulation loop | Carbon steel | 205.0 | 14.50 | general process service |
| HX-01-EXP | HTM expansion tank | R-rough to D-rough heat recovery HTM expansion and inventory hold-up | Carbon steel | 210.0 | 6.00 | general process service |
| HX-01-RV | HTM relief package | R-rough to D-rough heat recovery thermal relief and collection package | Carbon steel | 213.0 | 13.50 | general process service |
| HX-02 | Heat integration exchanger | D-rough to E-rough heat recovery | SS316 | 162.0 | 6.50 | general process service |
| HX-02-CTRL | Utility control package | D-rough to E-rough heat recovery control valves, instrumentation, and bypass station | Carbon steel | 158.0 | 5.00 | general process service |

### MoC Option Screening

| Candidate | Description | Score | Role | Feasible | Screening Notes |
| --- | --- | --- | --- | --- | --- |
| carbon_steel | Carbon steel construction | 100.00 | selected | yes | screening-feasible |
| ss316l | SS316L construction | 98.00 | alternate | yes | screening-feasible |
| alloy_steel_converter_service | Alloy steel converter service | 52.00 | alternate | yes | screening-feasible |
| rubber_lined_cs | Rubber-lined carbon steel | 58.00 | alternate | yes | screening-feasible |

### Equipment-Wise MoC Justification Matrix

| Equipment | Service Basis | Corrosion Driver | Selected MoC | Alternate MoC | Inspection / Cleaning Basis | Rationale |
| --- | --- | --- | --- | --- | --- | --- |
| R-101 | general process liquid service | elevated-temperature metal-loss allowance | Carbon Steel | SS316L construction | thickness survey + nozzle / tray / internals inspection | Carbon Steel retained for omega_catalytic because general process liquid service controls the screening basis. |
| PU-201 | general process liquid service | general aqueous-organic corrosion allowance basis | Carbon Steel | SS316L construction | thickness survey + nozzle / tray / internals inspection | Carbon Steel retained for omega_catalytic because general process liquid service controls the screening basis. |
| V-101 | general process liquid service | general aqueous-organic corrosion allowance basis | Carbon Steel | SS316L construction | periodic shell and connection inspection | Carbon Steel retained for omega_catalytic because general process liquid service controls the screening basis. |
| E-101 | thermal / utility service | thermal cycling, condensate, and fouling-side exposure | Carbon Steel | SS316L construction | tube-side fouling, rack shoe, and support expansion inspection | Carbon Steel retained for omega_catalytic because thermal / utility service controls the screening basis. |
| TK-301 | inventory / storage service | general aqueous-organic corrosion allowance basis | SS304 | Carbon steel construction | shell-floor, vent, and nozzle pad inspection | SS304 retained for omega_catalytic because inventory / storage service controls the screening basis. |
| HX-01 | thermal / utility service | thermal cycling, condensate, and fouling-side exposure | Carbon steel | SS316L construction | tube-side fouling, rack shoe, and support expansion inspection | Carbon steel retained for omega_catalytic because thermal / utility service controls the screening basis. |
| HX-01-CTRL | thermal / utility service | thermal cycling, condensate, and fouling-side exposure | Carbon steel | SS316L construction | tube-side fouling, rack shoe, and support expansion inspection | Carbon steel retained for omega_catalytic because thermal / utility service controls the screening basis. |
| HX-01-HDR | thermal / utility service | thermal cycling, condensate, and fouling-side exposure | Carbon steel | SS316L construction | tube-side fouling, rack shoe, and support expansion inspection | Carbon steel retained for omega_catalytic because thermal / utility service controls the screening basis. |
| HX-01-PMP | thermal / utility service | thermal cycling, condensate, and fouling-side exposure | Carbon steel | SS316L construction | tube-side fouling, rack shoe, and support expansion inspection | Carbon steel retained for omega_catalytic because thermal / utility service controls the screening basis. |
| HX-01-EXP | thermal / utility service | thermal cycling, condensate, and fouling-side exposure | Carbon steel | SS316L construction | tube-side fouling, rack shoe, and support expansion inspection | Carbon steel retained for omega_catalytic because thermal / utility service controls the screening basis. |
| HX-01-RV | thermal / utility service | thermal cycling, condensate, and fouling-side exposure | Carbon steel | SS316L construction | tube-side fouling, rack shoe, and support expansion inspection | Carbon steel retained for omega_catalytic because thermal / utility service controls the screening basis. |
| HX-02 | thermal / utility service | thermal cycling, condensate, and fouling-side exposure | SS316 | Carbon steel construction | tube-side fouling, rack shoe, and support expansion inspection | SS316 retained for omega_catalytic because thermal / utility service controls the screening basis. |
| HX-02-CTRL | thermal / utility service | thermal cycling, condensate, and fouling-side exposure | Carbon steel | SS316L construction | tube-side fouling, rack shoe, and support expansion inspection | Carbon steel retained for omega_catalytic because thermal / utility service controls the screening basis. |

### Inspection and Maintainability Basis

| Equipment | Service Basis | Inspection Basis | Maintainability Basis | Platform | Ladder |
| --- | --- | --- | --- | --- | --- |
| R-101 | general process liquid service | thickness survey + nozzle / tray / internals inspection | platform/ladder access with routine shell and nozzle inspection | yes | yes |
| PU-201 | general process liquid service | thickness survey + nozzle / tray / internals inspection | platform/ladder access with routine shell and nozzle inspection | yes | yes |
| V-101 | general process liquid service | periodic shell and connection inspection | platform/ladder access with routine shell and nozzle inspection | no | yes |
| E-101 | thermal / utility service | tube-side fouling, rack shoe, and support expansion inspection | rack access, expansion restraint checks, and isolation spool maintenance | yes | yes |
| TK-301 | inventory / storage service | shell-floor, vent, and nozzle pad inspection | shell-floor inspection, vent maintenance, and transfer-line isolation access | no | yes |
| HX-01 | thermal / utility service | tube-side fouling, rack shoe, and support expansion inspection | rack access, expansion restraint checks, and isolation spool maintenance | yes | yes |
| HX-01-CTRL | thermal / utility service | tube-side fouling, rack shoe, and support expansion inspection | rack access, expansion restraint checks, and isolation spool maintenance | no | no |
| HX-01-HDR | thermal / utility service | tube-side fouling, rack shoe, and support expansion inspection | rack access, expansion restraint checks, and isolation spool maintenance | no | no |
| HX-01-PMP | thermal / utility service | tube-side fouling, rack shoe, and support expansion inspection | rack access, expansion restraint checks, and isolation spool maintenance | no | no |
| HX-01-EXP | thermal / utility service | tube-side fouling, rack shoe, and support expansion inspection | rack access, expansion restraint checks, and isolation spool maintenance | no | no |
| HX-01-RV | thermal / utility service | tube-side fouling, rack shoe, and support expansion inspection | rack access, expansion restraint checks, and isolation spool maintenance | no | no |
| HX-02 | thermal / utility service | tube-side fouling, rack shoe, and support expansion inspection | rack access, expansion restraint checks, and isolation spool maintenance | yes | yes |
| HX-02-CTRL | thermal / utility service | tube-side fouling, rack shoe, and support expansion inspection | rack access, expansion restraint checks, and isolation spool maintenance | no | no |

### Corrosion and Service Basis

| Parameter | Value |
| --- | --- |
| Selected MoC decision | carbon_steel |
| Decision summary | Carbon steel construction selected as the highest-ranked alternative. |
| Route family service | omega_catalytic |
| Storage material | SS304 |
| Reactor material | Carbon Steel |
| Main separation material | Carbon Steel |

### Utility and Storage MoC Basis

| Service Class | Equipment | Typical MoC | Primary Driver | Piping / Connection Basis |
| --- | --- | --- | --- | --- |
| Storage and inventory systems | HX-01-EXP, TK-301 | Carbon steel, SS304 | inventory breathing, drainage, and shell-floor exposure | tank nozzle and vent classes follow selected vessel pressure class basis |
| Thermal and utility packages | E-101, HX-01, HX-01-CTRL, HX-01-EXP, HX-01-HDR, HX-01-PMP, HX-01-RV, HX-02, HX-02-CTRL | Carbon Steel, Carbon steel, SS316 | thermal cycling, condensation, and fouling-side service | utility headers and exchanger nozzles inherit screening connection classes from mechanical basis |
| Primary process vessels | PU-201, R-101 | Carbon Steel | core reaction / separation chemistry and cleanability | primary process connections follow equipment pressure class and nozzle reinforcement family |

### Nozzle and Connection Schedule

| Equipment | Pressure Class | Hydrotest (bar) | Reinforcement Family | Nozzle Services | Connection Classes | Orientations (deg) | Projections (mm) | Shell Factors | Load Cases (kN) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-101 | ASME 600 | 26.000 | integral repad | feed, product, utility, instrument | ASME 600, ASME 600, ASME 600, ASME 600 | 0, 90, 180, 270 | 9802.9, 9802.9, 9802.9, 9802.9 | 2.36, 2.36, 2.36, 2.36 | 60.10, 60.10, 60.10, 60.10 |
| PU-201 | PN16 | 3.000 | integral repad | feed, overhead, bottoms, instrument | PN16, PN16, PN16, PN16 | 0, 90, 180, 270 | 672.2, 672.2, 672.2, 672.2 | 1.85, 1.85, 1.85, 1.85 | 4.18, 4.18, 4.18, 4.18 |
| V-101 | PN16 | 4.000 | shell excess area | inlet, outlet, instrument | PN16, PN16, PN16 | 0, 180, 270 | 4112.9, 4112.9, 4112.9 | 1.74, 1.74, 1.74 | 32.99, 32.99, 32.99 |
| E-101 | ASME 150 | 10.400 | shell excess area | inlet, outlet, instrument | ASME 150, ASME 150, ASME 150 | 0, 180, 270 | 2122.0, 2122.0, 2122.0 | 1.80, 1.80, 1.80 | 17.77, 17.77, 17.77 |
| TK-301 | PN16 | 2.200 | shell excess area | inlet, outlet, vent | PN16, PN16, PN16 | 0, 180, 270 | 5436.2, 5436.2, 5436.2 | 1.78, 1.78, 1.78 | 43.28, 43.28, 43.28 |
| HX-01 | ASME 300 | 14.300 | set-on repad | inlet, outlet, instrument | ASME 300, ASME 300, ASME 300 | 0, 180, 270 | 2278.4, 2278.4, 2278.4 | 1.84, 1.84, 1.84 | 23.89, 23.89, 23.89 |
| HX-01-CTRL | ASME 150 | 11.700 | shell excess area | inlet, outlet, instrument | ASME 150, ASME 150, ASME 150 | 0, 180, 270 | 90.0, 90.0, 90.0 | 1.19, 1.19, 1.19 | 1.26, 1.26, 1.26 |
| HX-01-HDR | ASME 300 | 18.850 | set-on repad | inlet, outlet, branch, drain | ASME 300, ASME 300, ASME 300, ASME 300 | 0, 180, 270 | 521.3, 521.3, 521.3, 521.3 | 2.13, 2.13, 2.13, 2.13 | 5.62, 5.62, 5.62, 5.62 |
| HX-01-PMP | ASME 300 | 18.850 | set-on repad | inlet, outlet, instrument | ASME 300, ASME 300, ASME 300 | 0, 180, 270 | 146.7, 146.7, 146.7 | 1.45, 1.45, 1.45 | 3.87, 3.87, 3.87 |
| HX-01-EXP | ASME 150 | 7.800 | set-on repad | inlet, outlet, vent | ASME 150, ASME 150, ASME 150 | 0, 180, 270 | 218.9, 218.9, 218.9 | 1.44, 1.44, 1.44 | 3.13, 3.13, 3.13 |
| HX-01-RV | ASME 300 | 17.550 | set-on repad | inlet, outlet, instrument | ASME 300, ASME 300, ASME 300 | 0, 180, 270 | 181.8, 181.8, 181.8 | 1.49, 1.49, 1.49 | 4.04, 4.04, 4.04 |
| HX-02 | ASME 150 | 8.450 | shell excess area | inlet, outlet, instrument | ASME 150, ASME 150, ASME 150 | 0, 180, 270 | 644.4, 644.4, 644.4 | 1.69, 1.69, 1.69 | 5.87, 5.87, 5.87 |
| HX-02-CTRL | ASME 150 | 6.500 | shell excess area | inlet, outlet, instrument | ASME 150, ASME 150, ASME 150 | 0, 180, 270 | 90.0, 90.0, 90.0 | 1.12, 1.12, 1.12 | 0.80, 0.80, 0.80 |