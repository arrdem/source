// HyLoft 01031 Folding Storage TireLoft,

module rounded_cylinder(r, h, n) {
  rotate_extrude(convexity=1) {
    offset(r=n) offset(delta=-n) square([r,h]);
    square([n,h]);
  }
}

module tire(dia, w, iw) {
    difference() {
        rounded_cylinder(dia/2, w, 1);
        cylinder(r=(iw/2), h=w);
    }
}

module loft_end() {
    cube([1, 22.5, 1]);
    cube([1, 1, 24.5]);
    
    translate([-0.125, 22.5, -0.75])
    rotate([45, 0, 0])
    cube([0.125, 1, 32]);
}

module tire_loft() {
    color("silver") {
        loft_end();
        
        translate([0, 4, 0.5])
        rotate([0, 90, 0])
        cylinder(d=1, h=42);

        translate([0, 22, 0.5])
        rotate([0, 90, 0])
        cylinder(d=1, h=42);
        
        translate([42, 0, 0])
        mirror([1, 0, 0])
        loft_end();
    }

    // tires
    for(i=[0:10:30]) {
        let(dr=2) {
            translate([i + 1, (28.3/2)-dr, (28.3/2)-dr])
            rotate([0, 90])
            color("black")
            tire(28.3, 9.3, 19);
        }
    }
}

tire_loft();