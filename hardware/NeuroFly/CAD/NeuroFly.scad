// NeuroFly | Parametric FDM assembly | mm | OpenSCAD 2021.01+
// Select part=0 for the installed assembly, or a print ID listed in export.py.
part=0;
pose=undef;                    // override to inspect a particular absolute angle
base_width=200; base_depth=145; base_height=65;
wall_thickness=2.8; floor_t=3.2; lid_t=5;
print_tolerance=0.30;          // radial/per-side allowance on sliding profiles
screw_clearance=0.4;           // diametral addition for through fasteners
servo_body_width=40.7; servo_body_depth=19.7; servo_body_height=42.9;
servo_mount_spacing=[49.5,10]; // commissioning parameters, NOT manufacturer datums
servo_axis_from_end=10.0;      // short end of long case to spline centre
flange_to_horn_face=15;        // seated flange underside to flat horn outer face
ear_t=2.5; horn_t=2.2;         // sample assumptions; measure actual parts
horn_radii=[12,12];            // opposite holes on original double/cross arm
horn_slot_travel=2.0;
arm_length=150; arm_thickness=6; arm_rest_angle=15; arm_escape_angle=75;
fly_body_length=52;            // total, including integrated head
sensor_board_width=25.4; sensor_board_height=17.78; sensor_spacing=[20.32,12.7];
sensor_board_t=1.6; sensor_hole=2.5;
bearing_od=16; bearing_width=5; bearing_seat_extra=0.12; pin_socket=5.12;
m3_pilot=2.65; m25_pilot=2.12; m2_pilot=1.65; // tap/qualify on coupon
$fn=48; eps=.04;
W=base_width; D=base_depth; H=base_height; deck=H-lid_t;
px=W-74; py=D-46; lift=48; pz=H+lift; A=arm_thickness;
fl=-5-flange_to_horn_face; sc=servo_axis_from_end-servo_body_width/2;
pi_x=87.8; pi_y=D-3.5; pcb_z=15;
sx=44; sz=33;
bw=15+A-6; cheek=bw; rear=-11; front_gap=A+1; pin_base=A+8;
stop_a=[-18,109,230]; rr=33;
function uv(a,r)=[r*cos(a),r*sin(a)];
function lid_screws()=[[9,12],[W-9,11],[9,D-71],[W-59.5,D-4.1],[W-9,D-10]];
function mount_u()=[sc-21,sc+21];
function foot_w()=[fl-20,cheek+22];
module box(x,y,z,w,d,h){translate([x,y,z])cube([w,d,h]);}
module rod(x,y,z,d,h){translate([x,y,z])cylinder(d=d,h=h);}
module rr2(w,d,r){offset(r=r) translate([r,r])square([w-2*r,d-2*r]);}
module rect(x,y,z,w,d,h,r){translate([x,y,z])linear_extrude(h)rr2(w,d,r);}
module slot(x,y,z,dx,dy,d,h){hull(){rod(x-dx/2,y-dy/2,z,d,h);rod(x+dx/2,y+dy/2,z,d,h);}}
module local_drive(){multmatrix([[0,0,-1,px],[-1,0,0,py],[0,1,0,pz],[0,0,0,1]])children();}
module fly_frame(){multmatrix([[0,-1,0,arm_length],[0,0,1,12],[-1,0,0,A/2],[0,0,0,1]])children();}
module sensor_frame(){translate([sx,0,sz])rotate([90,0,0])children();}
module pi_nodes(){for(ix=[3.5,61.5],iy=[3.5,52.5])translate([pi_x-ix,pi_y-iy,0])children();}
module tie_pad(x,y){difference(){rect(x-6,y-4,floor_t-.2,12,8,4.6,1.5);box(x-2.1,y-5,floor_t,4.2,10,2.2);}}
module base(){
 difference(){
  union(){
   difference(){linear_extrude(deck)rr2(W,D,9);
    rect(wall_thickness,wall_thickness,floor_t,W-2*wall_thickness,D-2*wall_thickness,deck,9-wall_thickness);}
   for(q=lid_screws())hull(){rod(q.x,q.y,0,q.y>D-6?8:10,deck); // tie tall screw towers to closest wall
      if(q.y<20 || q.y>D-20)rod(q.x,q.y<20?wall_thickness:D-wall_thickness,0,4,deck);
      else rod(wall_thickness,q.y,0,4,deck);}
   pi_nodes()cylinder(d=6.3,h=pcb_z);
   for(x=[sx-29,sx+29])box(x-4.5,1,sz-5,9,8,10);
   for(q=[[152,34],[177,61],[174,D-14],[53,16]])tie_pad(q.x,q.y);
   // Low open raceway, fixed rear loom and terminal-block bed.
   for(x=[169,180])rect(x,70,floor_t-.2,2.2,45,5,0.8);
  }
  for(q=lid_screws())rod(q.x,q.y,deck-13,m3_pilot,14);
  pi_nodes()translate([0,0,pcb_z-8])cylinder(d=m25_pilot,h=9);
  // USB/Ethernet bank at left; Micro-USB / HDMI / audio at rear
  box(-1,pi_y-58,pcb_z-1,8,59,21);
  intersection(){box(0,pi_y-10,pcb_z-.2,9,12,2.9);
    rect(pi_x-85-.55,pi_y-56-.55,pcb_z-.15,86.1,57.1,2.8,3.55);}
  box(pi_x-63,D-7,pcb_z-1,61,9,13);
  rect(pi_x-11,pi_y-42,-1,37,29,floor_t+2,4); // underside microSD finger well
  for(x=[15:7:71])rect(x,D-47,-1,3,26,floor_t+2,1.4);
  for(q=[[17,25],[W-17,25],[W-18,D-17]])rod(q.x,q.y,-1,4.5,floor_t+2);
  // full plug passes above the cable tie anchor
  translate([W-26,D+1,22])rotate([90,0,0])cylinder(d=13,h=8);
  sensor_frame(){box(14,-6,-12,12,12,16);for(x=[-29,29])rod(x,0,-9,m3_pilot,11);}
  translate([96,.65,26])rotate([90,0,0])linear_extrude(.85)
     text("NeuroFly",size=9,font="Liberation Sans:style=Bold",spacing=1.04);
 }
}
module lid(){
 difference(){
  union(){linear_extrude(lid_t)rr2(W,D,9);
   // 4 mm underside ribs flanking the drive feet, 3 mm clear of chassis towers
   for(y=[py-21,py+19])rect(px-44,y,-4,94,3,4.3,1.45);
  }
  for(q=lid_screws())rod(q.x,q.y,-5,3+screw_clearance,12);
  for(u=mount_u(), w=foot_w()) // longitudinal adjustment on both feet
   slot(px-w,py-u,-5,3,0,4+screw_clearance,12);
  rect(px+52,py-12,-5,14,12,12,3);
  for(y=[py-21,py+9])rod(px+59,y,-5,m3_pilot,12);
  for(x=[16:7:79])rect(x,D-54,-5,3,39,12,1.45);
 }
}
module mount_profile(z,h){
 difference(){
   rect(sc-32,-16,z,64,32,h,3);
   box(sc-servo_body_width/2-print_tolerance,-servo_body_depth/2-print_tolerance,z-1,
       servo_body_width+2*print_tolerance,servo_body_depth+2*print_tolerance,h+2);
   // permit cable/strain relief to travel through upper part of end
   box(sc-servo_body_width/2-4, -3.5,z-1,5,7,h+2);
   box(sc+servo_body_width/2-1, -4,z-1,5,8,h+2);
   for(s=[-1,1],t=[-1,1])slot(sc+s*servo_mount_spacing.x/2,t*servo_mount_spacing.y/2,z-1,2,0,3.7,h+2);
 }
}
module foot(z0,z1,wc){
 difference(){box(sc-32,-lift,z0,64,6,z1-z0);
  for(u=mount_u())translate([u,-lift-1,wc])rotate([-90,0,0])cylinder(d=4+screw_clearance,h=9);}
}
module gusset(u,w1,w2){hull(){box(u,-lift,w1,4,5,w2-w1);box(u,-lift+27,w2-3,4,2,3);}}
module mount(){
 union(){
  mount_profile(fl-5,5);
  box(sc-32,-lift,fl-5,64,lift-15,5);
  foot(fl-28,fl,fl-20);
  for(u=[sc-31,sc+27])gusset(u,fl-28,fl);
 }
}
module disk_at(x,y,r){translate([x,y])circle(r=r);}
module bar2(p,q,r1,r2){hull(){disk_at(p.x,p.y,r1);disk_at(q.x,q.y,r2);}}
module arm(){
 difference(){
  linear_extrude(A)union(){
   circle(r=16.5);
   polygon([[0,-11],[arm_length,-4.3],[arm_length,4.3],[0,11]]);
   for(i=[-1,1])disk_at(arm_length+i*4,0,4.4);
  }
  // Alternating diagonal webs, rounded internal corners
  for(i=[0:5])let(x1=22+i*(arm_length-39)/6,x2=22+(i+1)*(arm_length-39)/6-4,
      a=8-6.7*x1/arm_length,b=8-6.7*x2/arm_length,t=(i%2==0?1:-1))
   translate([0,0,-1])linear_extrude(A+2)offset(r=.85)
      polygon([[x1,t*a],[x2,t*b],[i%2==0?x2:x1,-t*(i%2==0?b:a)]]);
  rod(0,0,-1,8.5,A+2);
  for(v=[-11,11])rod(0,v,-1,3+screw_clearance,A+2);
  for(i=[-1,1])rod(arm_length+i*4,0,-1,2.5+screw_clearance,A+2);
  // clearance for horn mounting bolt heads on face of adapter
  for(i=[0,1])slot((i==0?-1:1)*horn_radii[i],0,-.1,2*horn_slot_travel,0,5.5,2.6);
 }
}
module adapter(){
 difference(){
  rod(0,0,-5,33,5);
  rod(0,0,-6,8.5,7);
  for(i=[0,1])slot((i==0?-1:1)*horn_radii[i],0,-6,2*horn_slot_travel,0,2+screw_clearance,7);
  for(v=[-11,11]){rod(0,v,-6,3+screw_clearance,7);
    translate([0,v,-5.1])cylinder(d=5.75/cos(30),h=2.65,$fn=6);}
 }
}
module cap(){
 difference(){union(){linear_extrude(3.4)bar2([0,-11],[0,11],4.3,4.3);rod(0,0,0,10,8);}
  rod(0,0,1,pin_socket,8);for(v=[-11,11])rod(0,v,-1,3+screw_clearance,6);}
}
module stop_nodes(){for(a=stop_a)translate(uv(a,rr))children();}
module guard_outline(){
 difference(){union(){circle(r=41);
   polygon(concat([[0,0]],[for(a=[-38:2:128])uv(a,55)]));}circle(r=37.8);}
 stop_nodes()circle(r=6);
}
module stop_drill(){stop_nodes()translate([0,0,-25])cylinder(d=4+screw_clearance,h=55);}
module cheek_part(){
 difference(){union(){
  translate([0,0,cheek])linear_extrude(6) hull(){circle(r=41);translate([sc-32,-lift])square([64,2]);}
  rod(0,0,cheek+5.8,17,4.6);
  foot(cheek,cheek+30,cheek+22);
  for(u=[sc-31,sc+27])mirror([0,0,1])gusset(u,-cheek-30,-cheek);
 }
 rod(0,0,cheek-1,13,9);
 rod(0,0,cheek+5.9,8,3.2);
 rod(0,0,cheek-.1,bearing_od+bearing_seat_extra,bearing_width+.1);
 stop_drill();}
}
module guard_back(){
 difference(){union(){
   translate([0,0,rear])linear_extrude(2.2)union(){circle(r=41);
      polygon(concat([[0,0]],[for(a=[-38:2:128])uv(a,55)]));}
   translate([0,0,rear+2])linear_extrude(-1-(rear+2))guard_outline();}
  rod(0,0,rear-1,36,4);
  // stationary servo nose and original mounting bolt heads protrude through back
  rect(sc-servo_body_width/2-1,-servo_body_depth/2-1,rear-1,servo_body_width+2,servo_body_depth+2,4,2);
  for(s=[-1,1],t=[-1,1])rod(sc+s*servo_mount_spacing.x/2,t*servo_mount_spacing.y/2,rear-1,8,4);
  stop_drill();}
}
module guard_rim(){
 difference(){
 union(){
 translate([0,0,front_gap])linear_extrude(cheek-front_gap)guard_outline();
 translate([0,0,-1])linear_extrude(front_gap+1.05)difference(){guard_outline();
     polygon(concat([[0,0]],[for(a=[-26:2:116])uv(a,64)]));}
 }stop_drill();}
}
module connector(){
 difference(){union(){
   rect(arm_length-9,-3.8,A,18,15.8,4.6,2);
   box(arm_length-9,8.4,A/2-9,18,3.6,18);
  }
  for(i=[-1,1])rod(arm_length+i*4,0,A-.1,m25_pilot,5);
  translate([arm_length,7,A/2])rotate([-90,0,0])cylinder(d=3+screw_clearance,h=7);
 }
 // locating peg, placed along belly centreline
 translate([arm_length-6,11.9,A/2])rotate([-90,0,0])cylinder(d=2.6,h=2.6);
}
module blob(x,y,z,rx,ry,rz){translate([x,y,z])scale([rx,ry,rz])sphere(1,$fn=40);}
module fly_body(){
 scale([1,fly_body_length/52,1])difference(){
  union(){
   blob(0,-3,4,8.5,10,7); // thorax
   for(s=[0:3])blob(0,6+4.4*s,3.8,7.6-1.15*s,7.7-0.6*s,6.5-.7*s);
   blob(0,-16.3,5.5,8,9,7.2);
   for(t=[-1,1])blob(t*5.6,-19,6.8,4.5,5.5,5.3);
   // discrete wing landing pads with flat, keyed two-hole roots
   for(s=[-1,1])hull(){rod(6*s,-5.5,2,5.2,8.5);rod(6*s,.5,2,5.2,8.5);}
   rect(-5,-8,-.4,10,16,4,2);
  }
  box(-40,-40,-20,80,85,20);
  rod(0,0,-1,m3_pilot,8.4);
  rod(0,6/(fly_body_length/52),-.1,2.6+2*print_tolerance,3.3);
  for(s=[-1,1],y=[-5.5,.5])rod(6*s,y,4.3,m2_pilot,8);
  // trim roof over the pads
  for(s=[-1,1])box(s==1?3.4:-13,-9,10.5,9.6,13,6);
 }
}
module wing_right(){
 yy=fly_body_length/52;
 difference(){
 union(){
 linear_extrude(.8)hull(){
  disk_at(6,-5.5*yy,2.5);disk_at(6,.5*yy,2.5);
  disk_at(22,7,5.8);disk_at(30,21,5.6);disk_at(30,27,3.4);}
 linear_extrude(1.45)hull(){disk_at(6,-5.5*yy,2.5);disk_at(6,.5*yy,2.5);}
 translate([0,0,.7])linear_extrude(.65)union(){
 bar2([7,-5*yy],[29,14],.7,.5);bar2([29,14],[31,26],.5,.45);
 bar2([7,-3*yy],[22,12],.7,.52);bar2([22,12],[31,26],.52,.45);
 bar2([22,12],[28.8,14],.52,.48);}
 }
 for(y=[-5.5,.5])rod(6,y*yy,-1,2+screw_clearance,4);}
}
module carrier(){
 // native xy is front view, z projects towards viewer; mounts flush on front wall
 difference(){union(){rect(-34,-14,0,68,28,3,4);
   for(x=[-1,1],y=[-1,1])rod(x*sensor_spacing.x/2,y*sensor_spacing.y/2,2.8,4.9,3.2);}
 for(x=[-29,29])rod(x,0,-1,3+screw_clearance,6);
 for(x=[-1,1],y=[-1,1])rod(x*sensor_spacing.x/2,y*sensor_spacing.y/2,1.0,m2_pilot,7);
 rect(14,-6,-1,12,12,6,2); // keep the shell wiring interface stationary
 rect(-sensor_board_width/2+3,-sensor_board_height/2+4,-1,sensor_board_width-6,sensor_board_height-8,6,2);
 }
}
module wire_chimney(){
 difference(){union(){
    rect(-9,-8,0,18,16,31,4);
    rect(-9,-19,0,18,38,3.5,4);}
    rect(-7,-6,-1,14,12,34,2.8);
    for(y=[-15,15])rod(0,y,-1,3+screw_clearance,6);
    for(y=[-3.8,1.2])box(-12,y,23,24,2.6,4);
 }
}
module servo_dummy(){
 box(sc-servo_body_width/2,-servo_body_depth/2,-5-servo_body_height,servo_body_width,servo_body_depth,servo_body_height-6);
 difference(){box(sc-servo_mount_spacing.x/2-2.4,-servo_body_depth/2,fl,servo_mount_spacing.x+4.8,servo_body_depth,ear_t);
  for(s=[-1,1],t=[-1,1])rod(sc+s*servo_mount_spacing.x/2,t*servo_mount_spacing.y/2,fl-1,3.3,ear_t+2);}
 rod(0,0,-11.2,10,6.2-horn_t);
}
module horn_dummy(){difference(){translate([0,0,-5-horn_t])linear_extrude(horn_t)
  bar2([-horn_radii.x-1.5,0],[horn_radii.y+1.5,0],2.1,2.1);
  rod(0,0,-9,3,8);for(i=[0,1])rod((i==0?-1:1)*horn_radii[i],0,-9,2,8);}}
module bearing(){difference(){rod(0,0,cheek,16,5);rod(0,0,cheek-1,5,7);}}
module case_heads(){
 for(q=lid_screws())rod(q.x,q.y,H,5.5,2.8);
 for(u=mount_u(),w=foot_w()){rod(px-w,py-u,H+6,9,.8);rod(px-w,py-u,H+6.8,7,4);}
 for(y=[py-21,py+9])rod(px+59,y,H+3.5,5.5,2.8);
 sensor_frame(){for(x=[-29,29])rod(x,0,3,5.5,2.8);
 for(s=[-1,1],t=[-1,1])rod(s*sensor_spacing.x/2,t*sensor_spacing.y/2,6+sensor_board_t,3.8,1.6);}
 local_drive()for(s=[-1,1],t=[-1,1])translate([sc+s*servo_mount_spacing.x/2,t*servo_mount_spacing.y/2,fl+ear_t]){
 cylinder(d=8,h=.6);translate([0,0,.6])cylinder(d=5.5,h=3);}
}
module dampers(){for(i=[0,1])translate(uv(stop_a[i],rr))difference(){
 rod(0,0,-1,8,front_gap+1);rod(0,0,-2,4,front_gap+3);}}
// Simplified fastener envelopes. Smooth cylinders represent the nominal threads.
module rotor_fasteners(){
 for(v=[-11,11]){
  rod(0,v,A+3.4-14,3,14);rod(0,v,A+3.4,5.5,3);
  translate([0,v,-5])cylinder(d=5.5/cos(30),h=2.4,$fn=6);
 }
 for(i=[0,1])let(u=(i==0?-1:1)*horn_radii[i]){
  rod(u,0,-9.6,2,10);rod(u,0,0,5,.4);rod(u,0,.4,3.8,1.6);
  translate([u,0,-5-horn_t-1.6])cylinder(d=4/cos(30),h=1.6,$fn=6);
 }
 rod(0,0,-5,7,2.5);
 for(i=[-1,1]){
   rod(arm_length+i*4,0,0,2.5,10);rod(arm_length+i*4,0,-2,4.6,2);}
 fly_frame(){
   rod(0,0,-3.6,3,10);rod(0,0,-6,5.7,2.4);
   for(s=[-1,1],y=[-5.5,.5]){rod(6*s,y*fly_body_length/52,5.95,2,6);
     rod(6*s,y*fly_body_length/52,11.95,3.8,1.6);}
 }
}
module guard_fasteners(){stop_nodes(){
 rod(0,0,rear-.8,4,40);rod(0,0,rear-3.9,7.6,3.1);
 rod(0,0,rear-.8,9,.8);rod(0,0,cheek+6,9,.8);
 translate([0,0,cheek+6.8])cylinder(d=7/cos(30),h=5,$fn=6);
}}
module board(){difference(){rect(-sensor_board_width/2,-sensor_board_height/2,6,sensor_board_width,sensor_board_height,sensor_board_t,2.54);
 for(x=[-1,1],y=[-1,1])rod(x*sensor_spacing.x/2,y*sensor_spacing.y/2,5,sensor_hole,4);}}
module pi_dummy(){difference(){rect(pi_x-85,pi_y-56,pcb_z,85,56,1.6,3);pi_nodes()translate([0,0,pcb_z-1])cylinder(d=2.75,h=4);}}
module pi_ports(){for(y=[pi_y-47,pi_y-29,pi_y-10.25])box(pi_x-87,y-7.8,pcb_z+1.6,18,15.6,16);
 for(x=[10.6,32,53.5])box(pi_x-x-(x==32?8:4),pi_y-5,pcb_z+1.6,(x==32?16:8),7,6);}
module moving(a){
 rotate([0,0,a]){
 color("orange")arm();color("dimgray")adapter();color("gray")translate([0,0,A])cap();
 color("silver")rod(0,0,A+1,5,16);color("black")horn_dummy();color("silver")rotor_fasteners();
 color("gray")connector();fly_frame(){color("SandyBrown")fly_body();
 for(s=[-1,1])color("LightCyan")translate([0,0,10.5])scale([s,1,1])wing_right();}
 }}
module assembly(a){
 color("silver")case_heads();
 color("SlateGray")base();color("LightSlateGray")translate([0,0,deck])lid();
 color("DarkSlateGray")translate([px+59,py-6,H])wire_chimney();
 sensor_frame(){color("Teal")carrier();color("purple")board();color("black")box(-1.6,-1.3,6+sensor_board_t,3.2,2.6,1.5);}
 color("SeaGreen")pi_dummy();color("silver")pi_ports();
 local_drive(){color("DarkSlateGray")mount();color("DarkSlateGray")cheek_part();
 color("CadetBlue")guard_back();color("CadetBlue")guard_rim();color("Silver")bearing();
 color("Black")servo_dummy();color("Indigo")dampers();color("silver")guard_fasteners();moving(a);}
}
module bore_sample(){
 difference(){rect(0,0,0,52,19,5,2);
 for(i=[0:4])rod(6+10*i,9.5,-1,[m2_pilot,m25_pilot,m3_pilot,pin_socket,5.75/cos(30)][i],7,$fn=i==4?6:48);}
}
module bearing_sample(){difference(){rod(0,0,0,23,6);rod(0,0,-1,bearing_od+bearing_seat_extra,6);rod(0,0,-1,13,8);}}
assert(arm_length>=100 && arm_length<=180 && arm_thickness>=5 && arm_thickness<=8);
assert(arm_escape_angle>arm_rest_angle);
if(part==0)assembly(is_undef(pose)?arm_rest_angle:pose);
if(part==1)base();
if(part==2)translate([0,D,lid_t])rotate([180,0,0])lid();
if(part==3)translate([0,0,fl])rotate([180,0,0])mount();
if(part==4)arm();
if(part==5)translate([0,0,5])adapter();
if(part==6)fly_body();
if(part==8)mirror([1,0,0])wing_right();
if(part==9)wing_right();
if(part==10)translate([0,0,arm_length+9])rotate([0,90,0])connector();
if(part==11)carrier();
if(part==12)translate([0,0,-cheek])cheek_part();
if(part==13)cap();
if(part==14)translate([0,0,-rear])guard_back();
if(part==15)translate([0,0,cheek])rotate([180,0,0])guard_rim();
if(part==16)wire_chimney();
if(part==21)mount_profile(0,3);
if(part==22)translate([0,0,5])adapter(); // use in final assembly if fit passes
if(part==23)bearing_sample();
if(part==24)bore_sample();
