use <casters.scad>

module beam($fn=$fn) {
    union() {
        translate([2, 0, 0])
        cube([24, 2, 4]);
        translate([26, 0, 2])
        rotate([-90, 0, 0])
        cylinder(r=2, h=2, $fn=$fn);
    }
}

module top() {
    translate([0, 0, 4])
    cube([24, 96, 0.75]);
    
    translate([0, 2, 0])
    beam();
    
    translate([0, 48, 0])
    beam();

    translate([0, 94, 0])
    beam();
}


module worktop() {
    translate([0, 0, 40]) {
        translate([6, 0, 0])
        cube([14, 2, 4]);

        translate([6, 92, 0])
        cube([14, 2, 4]);

        top();

        // the wing
        translate([52, 96, 0])
        rotate([0, 0, 180])
        top();
        
        // supports
        translate([0, 0, -4]) {
        }
    }
    
    for(x=[2, 20])
    for(y=[0, 92])
    translate([x, y, 0])
    cube([4, 2, 44]);
    
    translate([6, 0, 0])
    cube([14, 2, 4]);
    
    translate([0, 2, 0])
    cube([24, 2, 4]);

    translate([6, 92, 0])
    cube([14, 2, 4]);
    
    translate([0, 94, 0])
    cube([24, 2, 4]);
}

worktop();