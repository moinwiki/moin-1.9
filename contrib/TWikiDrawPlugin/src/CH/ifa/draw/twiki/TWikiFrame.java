/*
 * @(#)TWikiDraw.java 5.1
 * Copyright 2000 by Peter Thoeny, Peter@Thoeny.com.
 * It is hereby granted that this software can be used, copied, 
 * modified, and distributed without fee provided that this 
 * copyright notice appears in all copies.
 * Portions Copyright (C) 2001 Motorola - All Rights Reserved
 */

package CH.ifa.draw.twiki;

import Acme.JPM.Encoders.*;
import CH.ifa.draw.appframe.*;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.*;
import CH.ifa.draw.figures.*;
import CH.ifa.draw.util.*;
import CH.ifa.draw.applet.*;
import CH.ifa.draw.contrib.*;
//import SVG.wiki.*;

import java.awt.*;
import java.awt.event.*;
import java.util.*;
import java.io.*;
import java.net.*;
import java.lang.reflect.*;

import com.keypoint.PngEncoderIndexed;

public class TWikiFrame extends DrawFrame {

    /**
     * Parameter names
     */
    static private String UNTITLED_PARAMETER   = "untitled";
    static private String DRAWPATH_PARAMETER   = "drawpath";
    static private String GIFPATH_PARAMETER    = "gifpath";
    static private String PNGPATH_PARAMETER    = "pngpath";
    static private String SVGPATH_PARAMETER    = "svgpath";
    static private String SAVEPATH_PARAMETER   = "savepath";
    static private String BASENAME_PARAMETER   = "basename";
    static private String HELPPATH_PARAMETER   = "helppath";
    static private String BORDERSIZE_PARAMETER = "bordersize";

    private Label fStatusLabel;

    public TWikiFrame(Application applet) {
        super("TWikiDraw", applet);

        this.view().setBackground(Color.white);

        // load	drawing
        if (applet.getParameter(DRAWPATH_PARAMETER) !=	null) {
            loadDrawing(DRAWPATH_PARAMETER);
        }
    }

    protected void populateMenuBar(MenuBar menuBar) {
        menuBar.add(createDrawingMenu());
        menuBar.add(createEditMenu());
        menuBar.add(createSelectionMenu());
        menuBar.add(createFillMenu());
        menuBar.add(createLineMenu());
	menuBar.add(createTextMenu());
	setMenuBar(menuBar);
    }

    protected CommandMenu createDrawingMenu() {
        CommandMenu menu = new CommandMenu("Drawing");

	menu.add(new NewDrawingCommand(this));
	menu.add(new ReloadDrawingCommand(this));
	menu.add(new SaveDrawingCommand(this));
	menu.add(new ExitDrawingCommand(this));

	return menu;
    }

    protected CommandMenu createEditMenu() {
        CommandMenu menu = new CommandMenu("Edit");

	menu.add(new DeleteCommand("Delete", view()));
	menu.add(new CutCommand("Cut", view()));
	menu.add(new CopyCommand("Copy", view()));
	menu.add(new PasteCommand("Paste", view()));
	menu.add(new ToggleGuidesCommand("Toggle guides", view()));

	return menu;
    }

    protected CommandMenu createSelectionMenu() {
        CommandMenu menu = new CommandMenu("Selection");

	menu.add(new DuplicateCommand("Duplicate", view()));
	menu.add(new GroupCommand("Group", view()));
	menu.add(new UngroupCommand("Ungroup", view()));
	menu.add(new SendToBackCommand("Send to Back", view()));
	menu.add(new BringToFrontCommand("Bring to Front", view()));

        CommandMenu align = new CommandMenu("Align");
	align.add(new AlignCommand("Lefts", view(), AlignCommand.LEFTS));
	align.add(new AlignCommand("Centres", view(), AlignCommand.CENTERS));
	align.add(new AlignCommand("Rights", view(), AlignCommand.RIGHTS));
	align.add(new AlignCommand("Tops", view(), AlignCommand.TOPS));
	align.add(new AlignCommand("Middles", view(), AlignCommand.MIDDLES));
	align.add(new AlignCommand("Bottoms", view(), AlignCommand.BOTTOMS));
	menu.add(align);

	return menu;
    }

    protected CommandMenu createFillMenu() {
        CommandMenu menu = new CommandMenu("Fill");
        menu.add(createColorMenu("FillColor"));
	return menu;
    }

    protected CommandMenu createLineMenu() {
        CommandMenu menu = new CommandMenu("Line");

        menu.add(createColorMenu("FrameColor"));

	CommandMenu arrowStyle = new CommandMenu("Arrows");
        arrowStyle.add(
	    new ChangeAttributeCommand(
		"none", "ArrowMode", 
		new Integer(PolyLineFigure.ARROW_TIP_NONE),  view()));
        arrowStyle.add(
	    new ChangeAttributeCommand(
		"at Start", "ArrowMode",
		new Integer(PolyLineFigure.ARROW_TIP_START), view()));
        arrowStyle.add(
	    new ChangeAttributeCommand(
		"at End",   "ArrowMode",
		new Integer(PolyLineFigure.ARROW_TIP_END),   view()));
        arrowStyle.add(
	    new ChangeAttributeCommand(
		"at Both ends",  "ArrowMode",
		new Integer(PolyLineFigure.ARROW_TIP_BOTH),  view()));
	menu.add(arrowStyle);

	return menu;
    }

    protected CommandMenu createTextMenu() {
        CommandMenu menu = new CommandMenu("Text");

        menu.add(createFontMenu());
        menu.add(createColorMenu("TextColor"));

        CommandMenu style = new CommandMenu("Style");
        style.add(new ChangeAttributeCommand(
	    "Plain", "FontStyle", new Integer(Font.PLAIN),  view()));
        style.add(new ChangeAttributeCommand(
	    "Italic","FontStyle", new Integer(Font.ITALIC), view()));
        style.add(new ChangeAttributeCommand(
	    "Bold",  "FontStyle", new Integer(Font.BOLD),   view()));
	menu.add(style);

        CommandMenu align = new CommandMenu("Align");
        align.add(new ChangeAttributeCommand(
	    "Left", "TextAlign", "Left",  view()));
        align.add(new ChangeAttributeCommand(
	    "Centre", "TextAlign", "Centre", view()));
        align.add(new ChangeAttributeCommand(
	    "Right",  "TextAlign", "Right",   view()));
	menu.add(align);

	return menu;
    }

    //-- DrawFrame overrides -----------------------------------------

    protected void populateWestPanel(Panel palette) {
	// get the default selection tool
        super.populateWestPanel(palette);

        Tool tool = new TextTool(view(), new TextFigure());
        palette.add(createToolButton(IMAGES+"TEXT", "Text Tool", tool));

        tool = new ConnectedTextTool(view(), new TextFigure());
        palette.add(createToolButton(IMAGES+"ATEXT", "Connected Text Tool", tool));

        tool = new CreationTool(view(), new RectangleFigure());
        palette.add(createToolButton(IMAGES+"RECT", "Rectangle Tool", tool));

        tool = new CreationTool(view(), new RoundRectangleFigure());
        palette.add(createToolButton(IMAGES+"RRECT", "Round Rectangle Tool", tool));

        tool = new CreationTool(view(), new EllipseFigure());
        palette.add(createToolButton(IMAGES+"ELLIPSE", "Ellipse Tool", tool));

        tool = new CreationTool(view(), new LineFigure());
        palette.add(createToolButton(IMAGES+"LINE", "Line Tool", tool));

        tool = new ConnectionTool(view(), new LineConnection());
        palette.add(createToolButton(IMAGES+"CONN", "Connection Tool", tool));

        tool = new ConnectionTool(view(), new ElbowConnection());
        palette.add(createToolButton(IMAGES+"OCONN", "Elbow Connection Tool", tool));

        tool = new ScribbleTool(view());
        palette.add(createToolButton(IMAGES+"SCRIBBL", "Scribble Tool", tool));

        tool = new PolygonTool(view());
        palette.add(createToolButton(IMAGES+"POLYGON", "Polygon Tool", tool));

        tool = new BorderTool(view());
        palette.add(createToolButton(IMAGES+"BORDDEC", "Border Tool", tool));

        tool = new URLTool(view(), new RectangleFigure());
        palette.add(createToolButton(IMAGES+"URL", "URL Tool", tool));
    }

    protected Panel createSouthPanel() {
	Panel split = new Panel();
        split.setLayout(new GridLayout(2, 1));
	return split;
    }

    protected void populateSouthPanel(Panel panel) {
	Panel buttons = new Panel();
        Button button;

        button = new CommandButton(new DeleteCommand("Delete", view()));
        buttons.add(button);

        button = new CommandButton(new DuplicateCommand("Duplicate", view()));
        buttons.add(button);

        button = new CommandButton(new GroupCommand("Group", view()));
        buttons.add(button);

        button = new CommandButton(new UngroupCommand("Ungroup", view()));
        buttons.add(button);

        button = new CommandButton(new BringToFrontCommand("Bring To Front", view()));
        buttons.add(button);

        button = new CommandButton(new SendToBackCommand("Send To Back", view()));
        buttons.add(button);

        button = new Button("Help");
	button.addActionListener(
	    new ActionListener() {
		    public void actionPerformed(ActionEvent event) {
			showHelp();
		    }
		}
	    );
        buttons.add(button);
	panel.add(buttons);
	fStatusLabel = new Label("Status");
	panel.add(fStatusLabel);
    }

    public void showStatus(String s) {
	if (fStatusLabel != null)
	    fStatusLabel.setText(s);
	else
	    getApplication().showStatus(s);
    }

    /**
     * Workaround to get it work without update button
     */
    protected void setSimpleDisplayUpdate() {}
    protected void setBufferedDisplayUpdate() {}


    //-- actions -----------------------------------------

    protected void showHelp() {
        try {
            // gets help file path
            String helpPath =
		getApplication().getParameter(HELPPATH_PARAMETER);
            if (helpPath != null) {
                URL url = getApplication().getURL(helpPath);
                getApplication().popupFrame(url, "Help");
            }
        } catch (IOException e) {
            showStatus("Help file not found");
        }
    }

    class NewDrawingCommand extends Command {
	TWikiFrame frame;
	public NewDrawingCommand(TWikiFrame frm) {
	    super("Clear");
	    frame = frm;
	}
        public void execute() {
	    frame.doLoadDrawing(UNTITLED_PARAMETER);
	}
    }

    class ReloadDrawingCommand extends Command {
	TWikiFrame frame;
	public ReloadDrawingCommand(TWikiFrame frm) {
	    super("Reload");
	    frame = frm;
	}
        public void execute() {
	    frame.doLoadDrawing(DRAWPATH_PARAMETER);
	}
    }

    class SaveDrawingCommand extends Command {
	TWikiFrame frame;
	public SaveDrawingCommand(TWikiFrame frm) {
	    super("Save and Exit");
	    frame = frm;
	}
        public void execute() {
	    if (frame.doSaveDrawing())
		((TWikiDraw)getApplication()).exitApplet();
	}
    }

    class ExitDrawingCommand extends Command {
	TWikiFrame frame;
	public ExitDrawingCommand(TWikiFrame frm) {
	    super("Exit without saving");
	    frame = frm;
	}
        public void execute() {
	    ((TWikiDraw)getApplication()).exitApplet();
	}
    }

    public void doLoadDrawing(String name) {
		loadDrawing(name);
		view().setBackground(Color.white);
    }
	
    public boolean doSaveDrawing() {
		TWikiDraw app = (TWikiDraw)getApplication();
		boolean savedDraw, savedSvg, savedGif, savedPng, savedMap;
		savedDraw = savedSvg = savedGif = savedPng = savedMap = false;
		
		// set wait cursor
		setCursor(new Cursor(Cursor.WAIT_CURSOR));
		
		try {
			// saves the drawing to the stream of bytes
			ByteArrayOutputStream out = new ByteArrayOutputStream();
			StorableOutput output = new StorableOutput(out);
            // drawing() (class DrawFrame) returns the Drawing element
            // Drawing is a StandardDrawing (extends Drawing
			// and implements CompositeFigures)
			output.writeStorable(drawing());
			output.close();
			
			// gets pathname of the drawing
			String drawingPath = app.getParameter(DRAWPATH_PARAMETER);
			if (drawingPath == null)
				drawingPath = "untitled.draw";
			
			// gets script name
			String savePath = app.getParameter(SAVEPATH_PARAMETER);
			if (savePath == null)
				savePath = "";
			
			// gets base filename
			String baseName = app.getParameter(BASENAME_PARAMETER);
			if (baseName == null)
				baseName = "SET_BASENAME_PARAM";
			
			// submit POST command to the server three times:
			// *.draw, *.map and *.gif
			// first upload *.draw file
			showStatus("Saving " + baseName + ".draw");
			savedDraw = app.post(savePath, baseName + ".draw", "text/plain", drawingPath,
								 out.toString(), "TWikiDraw draw file");
			
			// calculate the minimum size of the gif image
			Dimension d = new Dimension(0, 0); // not this.view().getSize();
			FigureEnumeration k = drawing().figuresReverse();
			while (k.hasMoreElements()) {
				Figure figure = k.nextFigure();
				Rectangle r = figure.displayBox();
				if (r.x + r.width > d.width) {
					d.setSize(r.x + r.width, d.height);
				}
				if (r.y + r.height > d.height) {
					d.setSize(d.width, r.y + r.height);
				}
			}
			
			// gets add border size
			int iBorder = 10;
			String sBorder = getApplication().getParameter(BORDERSIZE_PARAMETER);
			if (sBorder != null) {
				iBorder = Integer.valueOf(sBorder).intValue();
				if (iBorder < 0) {
					iBorder = 0;
				}
			}
			
			String map = drawing().getMap();
			if (map.length() > 0) {
				String mapPath = drawingPath.substring(0, drawingPath.length() - 5);
				showStatus("Saving " + baseName + ".map");
				// enclose the map and add editable border. Note that the
				// edit border is add LAST so the earlier AREAs take
				// precedence.
				map = "<map name=\"%MAPNAME%\">\n" + map +
					"<area shape=\"rect\" coords=\"" +
					"0,0," + (d.width + iBorder) + "," + (iBorder/2) +
					"\" href=\"%TWIKIDRAW%\" />\n" +
					"<area shape=\"rect\" coords=\"" +
					"0,0," + (iBorder/2) + "," + (d.height + iBorder) +
					"\" href=\"%TWIKIDRAW%\" />\n" +
					"<area shape=\"rect\" coords=\"" +
					(d.width + iBorder/2) + ",0," + (d.width + iBorder) + "," + (d.height + iBorder) +
					"\" href=\"%TWIKIDRAW%\" />\n" +
					"<area shape=\"rect\" coords=\"" +
					"0," + (d.height + iBorder/2) + "," +
					(d.width + iBorder) + "," + (d.height + iBorder) +
					"\" href=\"%TWIKIDRAW%\" />\n" +
					"</map>";
				savedMap = app.post(savePath, baseName + ".map", "text/plain", mapPath + ".map",
									map, "TWikiDraw map file");
			} else {
				// erase any previous map file
				String mapPath = drawingPath.substring(0, drawingPath.length() - 5);
				savedMap = app.post( savePath, baseName + ".map", "text/plain", mapPath + ".map", "", "");
            }
			
            // get pathname of the SVG file
			/*
			  String svgPath = getApplication().getParameter(SVGPATH_PARAMETER);
			  if (svgPath != null && svgPath.length() > 0) {
			  showStatus("Saving " + svgPath);
			  // create the svg data
			  String outsvg = SvgSaver.convertSVG(out.toString());
			  // now upload *.svg file
			  savedSvg = app.post(savePath, "", "image/svg", svgPath,
			  outsvg, "SVG file");
			  }
			*/
			
			// gets pathname of the GIF image
			String gifPath = getApplication().getParameter(GIFPATH_PARAMETER);
			if (gifPath == null || gifPath.length() == 0) gifPath = null;
			
			// gets pathname of the PNG image
			String pngPath = getApplication().getParameter(PNGPATH_PARAMETER);
			if (pngPath == null || pngPath.length() == 0) pngPath = null;
			
			if (gifPath != null || pngPath != null) {
				// clear the selection so it doesn't appear
				view().clearSelection();
				
				Image oImgBuffer =
					this.view().createImage(d.width + iBorder, d.height + iBorder);
				Graphics oGrf = oImgBuffer.getGraphics();
				this.view().enableGuides(false);
				this.view().drawAll(oGrf);
				
				if (pngPath != null) {
					// then create *.png image and upload file
					showStatus("Saving " + baseName + ".png");
					
					PngEncoderIndexed oEncode = new PngEncoderIndexed(oImgBuffer);
					byte[] aByte = oEncode.pngEncode();
					int size = aByte.length;
					char[] aChar = new char[size];
					for(int i = 0; i < size; i++) {
						aChar[i] = (char)aByte[i];
					}
					
					// upload *.png file
					savedPng = app.post(savePath, baseName + ".png", "image/png",
										pngPath, String.valueOf( aChar, 0, size),
										"TWikiDraw PNG file");
				}
				
				if (gifPath != null) {
					// then create *.gif image and upload file
					showStatus("Saving " + baseName + ".gif");
					
					ByteArrayOutputStream oOut = new ByteArrayOutputStream();
					GifEncoder oEncode = new GifEncoder(oImgBuffer, oOut);
					oEncode.encode();
					byte[] aByte = oOut.toByteArray();
					int size = oOut.size();
					char[] aChar = new char[size];
					for(int i = 0; i < size; i++) {
						aChar[i] = (char)aByte[i];
					}
					
					// upload *.gif file
					savedGif = app.post(savePath, baseName + ".gif", "image/gif",
										gifPath, String.valueOf( aChar, 0, size),
										"TWikiDraw GIF file");
				}
			}
		} catch (MalformedURLException e) {
            this.setCursor(new Cursor(Cursor.DEFAULT_CURSOR));
            showStatus("Bad Wiki servlet URL: "+e.getMessage());
		} catch (IOException e) {
			e.printStackTrace();
			this.setCursor(new Cursor(Cursor.DEFAULT_CURSOR));
			showStatus(e.toString());
		}
		this.setCursor(new Cursor(Cursor.DEFAULT_CURSOR));
		showStatus("Saved .draw " + (savedDraw ? "OK" : "Failed") +
				   " .map " + (savedMap ? "OK" : "Failed") +
				   " .gif " + (savedGif ? "OK" : "Failed") +
				   " .png " + (savedPng ? "OK" : "Failed"));
		return savedDraw;
	}

}
