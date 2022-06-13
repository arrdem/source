// 2x4" nominal lumber is really 38mm x 89mm x Z
// Drawing unit: MM 1:1

use <casters.scad>

function in2mm(x) = 25.4 * x;

module txf(height) {
    cube([38, 89, height]);
}

module post(height) {
    txf(height);
}

module dpost(height) {
    post(height);

    translate([38, 0, 0])
    post(height);
}

module frame(width, depth, height) {
    translate([38, 38, 0]) {
        dpost(height);
    }

    translate([38, 38 + 89 + in2mm(30), 0]) {
        dpost(height);
    }

    translate([38, depth - 89 - 38, 0]) {
        dpost(height);
    }
    
    // bottom bar
    translate([0, 0, 89])
    rotate([-90, 0, 0])
    txf(depth);

    // top bar
    let(inset=in2mm(30) + 38 + 89) {
        translate([0, inset, height])
        rotate([-90, 0, 0])
        txf(depth - inset);
    }
    
    // support
    translate([0, 0, height - in2mm(20)])
    rotate([-90, 0, 0])
    txf(in2mm(30) + 38 * 2 + 89 * 2);
}

module shelf(width, depth, thickness) {
    // FIXME: Is there more shelf geometry? A bottom box in 1x2 or something?
    cube([width, depth, thickness]);
}

module bench(width, depth, height, 
             top_thickness=in2mm(0.75),
             shelf_width=in2mm(30),
             shelf_depth=in2mm(20)) {
    ch = 38 * 2 + 2;
    ph = height - ch - top_thickness;
    
    // The frame, at relative to caster plane coordinates.
    translate([0, 0, ch]) {
        frame(width, depth, ph);
        
        translate([width, 0, 0])
        mirror([1, 0, 0])
        frame(width, depth, ph);
    
        // top
        translate([0, 38 + 89 + in2mm(30), ph]) {
            cube([width, depth - 38 - 89 - shelf_width, top_thickness]);
        }

        translate([0, 0, ph]) {
            cube([width, 38 + 89, top_thickness]);
        }
        
        // Wing top
        
        // bottom bars
        translate([38, 38, 89])
        rotate([-90, 0, -90])
        txf(width - 38 * 2);

        translate([38, depth, 89])
        rotate([-90, 0, -90])
        txf(width - 38 * 2);
        
        // "top" bars
        translate([38, 38, ph - shelf_depth])
        rotate([-90, 0, -90])
        txf(width - 38 * 2);
        
        translate([38, 38, ph])
        rotate([-90, 0, -90])
        txf(width - 38 * 2);


        translate([38, 38, ph - shelf_depth])
        rotate([-90, 0, -90])
        txf(width - 38 * 2);
        
        translate([38, 38*2 + 89*2 + shelf_width, ph - in2mm(20)])
        rotate([-90, 0, -90])
        txf(width - 38 * 2);
        
        translate([38, 38*2 + 89*2 + shelf_width, ph])
        rotate([-90, 0, -90])
        txf(width - 38 * 2);

        translate([38, depth, ph])
        rotate([-90, 0, -90])
        txf(width - 38 * 2);
        
        // Reference shelf
        translate([0, 38 + 89, ph - shelf_depth/2])
        shelf(width, shelf_width, top_thickness);

    }
    
    // The casters, at absolute coordinates
    
    for (dx=[0, width-(38*3)])
    for (dy=[38, 38 + 89 + in2mm(30), depth-38-89])
    translate([dx + 38, dy + 89/2, 0])
    caster(
        // wheel (r, h)
        38, 30, 
        // axel (r, h)
        5, 1,
        // bearing (r, h)
        10, 1,
        $fn=16
    );
}


module worktop2() {
    // 1:1mm to 1:1in because I want to consume this model in the 1:1in garage sketch
    scale([1/25.4, 1/25.4, 1/25.4]) {
        bench(in2mm(32), in2mm(96), in2mm(40), in2mm(0.75));
    }
}

worktop2();