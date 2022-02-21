function sorted(arr) = !(len(arr)>0) ? [] : let(
    pivot   = arr[floor(len(arr)/2)],
    lesser  = [ for (y = arr) if (y  < pivot) y ],
    equal   = [ for (y = arr) if (y == pivot) y ],
    greater = [ for (y = arr) if (y  > pivot) y ]
) concat(
    sorted(lesser), equal, sorted(greater)
);

module ccube(dimensions) {
    ds = sorted(dimensions);
    echo(ds.y, ds.z, 1, "// thickness", ds.x);
    cube(dimensions);
}

module topbottom(dimensions, thickness, back_inset) {
    ccube([dimensions.x + (thickness * 2), dimensions.y + (thickness * 2) + back_inset, thickness]);
}

module side(dimensions, thickness) {
    ccube([thickness, dimensions.y, dimensions.z]);
}

module frontback(dimensions, thickness) {
    ccube([dimensions.x + (thickness * 2), thickness, dimensions.z]);
}

module box(dimensions, thickness, back_inset=0) {    
    translate([0, 0, 0]);
    topbottom(dimensions, thickness, back_inset);
    
    translate([0, 0, dimensions.z + thickness])
    topbottom(dimensions, thickness, back_inset);
    
    translate([0, thickness, thickness])
    side(dimensions, thickness);

    translate([dimensions.x + thickness, thickness, thickness])
    side(dimensions, thickness);
    
    translate([0, dimensions.y + thickness, thickness])
    frontback(dimensions, thickness);
    
    translate([0, thickness, thickness])
    rotate([0, 0, -15])
    mirror([0, 1, 0])
    frontback(dimensions, thickness);
}

box([5, 5, 5], 0.5, 1);
