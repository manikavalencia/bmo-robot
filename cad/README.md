# BMO Enclosure 3D Models

All physical chassis parts, bezels, and mounts for the BMO companion robot were modeled in Onshape.

## Source CAD & Direct Exports
You can view, inspect, and export fresh STL or STEP files directly from the live CAD workspace:
👉 https://cad.onshape.com/documents/c7c0f712962ecf7393a5a24b/w/503208ce2dbcedbb0cdd25ca/e/2d3898897f50a861de68ee02?renderMode=0&leftPanel=false&uiState=6af0015df3dc09af14678004

## A Note on STL Mesh Artifacts
If you download the pre-exported STLs in this repository and notice random faint lines or streaks across curved surfaces in basic 3D viewers, **do not worry**. These are purely visual rendering artifacts caused by triangle tessellation (how polygon meshes handle curves), not actual flaws in the Onshape geometry. 

When you drop these STLs into a slicer (like PrusaSlicer or Cura), the layer generator parses the underlying math cleanly, and your printed parts will come out completely smooth.

<img width="711" height="638" alt="bmo_preview" src="https://github.com/user-attachments/assets/28acc4b6-4a1d-4712-bdaf-eaa244ae8c1a" />

