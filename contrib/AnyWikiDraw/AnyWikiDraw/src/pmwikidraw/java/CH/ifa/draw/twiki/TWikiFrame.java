/*
 * @(#)TWikiDraw.java 5.1 Copyright 2000 by Peter Thoeny, Peter@Thoeny.com. It
 * is hereby granted that this software can be used, copied, modified, and
 * distributed without fee provided that this copyright notice appears in all
 * copies. Portions Copyright (C) 2001 Motorola - All Rights Reserved
 */

package CH.ifa.draw.twiki;

import Acme.JPM.Encoders.*;
//TODO: import com.eteks.filter.Web216ColorsFilter;

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
import java.awt.image.FilteredImageSource;

public class TWikiFrame extends DrawFrame
{

  /**
   * Parameter names
   */
  static private String UNTITLED_PARAMETER     = "untitled";

  static private String PAGENAME_PARAMETER     = "pagename";

  static private String HELPPATH_PARAMETER     = "helppath";

  static private String BORDERSIZE_PARAMETER   = "bordersize";

  static private String TRUEFILENAME_PARAMETER = "truefilename";

  static private String DRAWLOADPATH_PARAMETER = "drawingloadpath";  
  
  //CJ Added.
  static private String DRAWINGNAME_PARAMETER = "drawingname";
  
  static String DEBUG_PARAMETER = "debug";

  static private String WIDTH_PARAMETER = "width";

  static private String HEIGHT_PARAMETER = "height";

  static private String INLINE_PARAMETER = "inline";
  
  private TextField         fStatusLabel;

  // post can be disabled for testing
  private boolean       bPostEnabled           = true;

  public TWikiFrame(Application applet, String colors)
  {
    super("PmWikiDraw - " + applet.getParameter(DRAWINGNAME_PARAMETER), applet);
//    this.view().setBackground(Color.white);
    this.addWindowListener(new WindowAdapter() {
    	/* (non-Javadoc)
	     * @see java.awt.event.WindowAdapter#windowClosed(java.awt.event.WindowEvent)
	     */
	    public void windowClosing(WindowEvent e)
	    {
	      new ExitDrawingCommand(TWikiFrame.this).execute();
	    }
    });


    // Add a floating toolbar.
/*    Frame toolFrame = new Frame("Tools");
    Panel palette = new Panel();
    populateWestPalette(palette);
    toolFrame.add(palette);
    toolFrame.pack();
    toolFrame.setVisible(true);
  */  

    // load drawing
    if (applet.getParameter(DRAWLOADPATH_PARAMETER) != null)
    {
      loadDrawing(DRAWLOADPATH_PARAMETER);
    }
    
  }

  protected void populateMenuBar(MenuBar menuBar)
  {
    menuBar.add(createDrawingMenu());
    menuBar.add(createEditMenu());
    menuBar.add(createSelectionMenu());
    menuBar.add(createFillMenu());
    menuBar.add(createLineMenu());
    menuBar.add(createTextMenu());
    setMenuBar(menuBar);
    setBackground(new Color(192, 192, 192));
  }

  protected CommandMenu createDrawingMenu()
  {
    CommandMenu menu = new CommandMenu("Drawing");

    menu.add(new NewDrawingCommand(this));
    menu.add(new ReloadDrawingCommand(this));
    menu.add(new SaveDrawingCommand(this));
    menu.add(new ExitDrawingCommand(this));
    
    return menu;
  }

  protected CommandMenu createEditMenu()
  {
    CommandMenu menu = new CommandMenu("Edit");

    menu.add(new DeleteCommand("Delete", view()));
    menu.add(new CutCommand("Cut", view()));
    menu.add(new CopyCommand("Copy", view()));
    menu.add(new PasteCommand("Paste", view()));
    menu.add(new ToggleGuidesCommand("Toggle guides", view()));

    return menu;
  }

  protected CommandMenu createSelectionMenu()
  {
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

  protected CommandMenu createFillMenu()
  {
    CommandMenu menu = new CommandMenu("Fill");
    menu.add(createColorMenu("FillColor"));
    return menu;
  }

  protected CommandMenu createLineMenu()
  {
    CommandMenu menu = new CommandMenu("Line");

    menu.add(createColorMenu("FrameColor"));

    CommandMenu arrowStyle = new CommandMenu("Arrows");
    arrowStyle.add(new ChangeAttributeCommand("none", "ArrowMode", new Integer(
        PolyLineFigure.ARROW_TIP_NONE), view()));
    arrowStyle.add(new ChangeAttributeCommand("at Start", "ArrowMode",
        new Integer(PolyLineFigure.ARROW_TIP_START), view()));
    arrowStyle.add(new ChangeAttributeCommand("at End", "ArrowMode",
        new Integer(PolyLineFigure.ARROW_TIP_END), view()));
    arrowStyle.add(new ChangeAttributeCommand("at Both ends", "ArrowMode",
        new Integer(PolyLineFigure.ARROW_TIP_BOTH), view()));
    menu.add(arrowStyle);

    return menu;
  }

  protected CommandMenu createTextMenu()
  {
    CommandMenu menu = new CommandMenu("Text");

    menu.add(createFontMenu());
    menu.add(createColorMenu("TextColor"));

    CommandMenu style = new CommandMenu("Style");
    style.add(new ChangeAttributeCommand("Plain", "FontStyle", new Integer(
        Font.PLAIN), view()));
    style.add(new ChangeAttributeCommand("Italic", "FontStyle", new Integer(
        Font.ITALIC), view()));
    style.add(new ChangeAttributeCommand("Bold", "FontStyle", new Integer(
        Font.BOLD), view()));
    menu.add(style);

    CommandMenu align = new CommandMenu("Align");
    align.add(new ChangeAttributeCommand("Left", "TextAlign", "Left", view()));
    align.add(new ChangeAttributeCommand("Centre", "TextAlign", "Centre",
        view()));
    align
        .add(new ChangeAttributeCommand("Right", "TextAlign", "Right", view()));
    menu.add(align);

    return menu;
  }

  //-- DrawFrame overrides -----------------------------------------
 
  protected void populateWestPanel(Panel palette)
  {
    // get the default selection tool
    super.populateWestPanel(palette);

    Tool tool = new TextTool(view(), new TextFigure());
    palette.add(createToolButton(IMAGES + "TEXT", "Text Tool", tool));

    tool = new ConnectedTextTool(view(), new TextFigure());
    palette
        .add(createToolButton(IMAGES + "ATEXT", "Connected Text Tool", tool));

    tool = new CreationTool(view(), new RectangleFigure());
    palette.add(createToolButton(IMAGES + "RECT", "Rectangle Tool", tool));

    tool = new CreationTool(view(), new RoundRectangleFigure());
    palette
        .add(createToolButton(IMAGES + "RRECT", "Round Rectangle Tool", tool));

    tool = new CreationTool(view(), new EllipseFigure());
    palette.add(createToolButton(IMAGES + "ELLIPSE", "Ellipse Tool", tool));

    tool = new CreationTool(view(), new LineFigure());
    palette.add(createToolButton(IMAGES + "LINE", "Line Tool", tool));

    tool = new ConnectionTool(view(), new LineConnection());
    palette.add(createToolButton(IMAGES + "CONN", "Connection Tool", tool));

    tool = new ConnectionTool(view(), new ElbowConnection());
    palette.add(createToolButton(IMAGES + "OCONN", "Elbow Connection Tool",
        tool));

    tool = new ScribbleTool(view());
    palette.add(createToolButton(IMAGES + "SCRIBBL", "Scribble Tool", tool));

    tool = new PolygonTool(view());
    palette.add(createToolButton(IMAGES + "POLYGON", "Polygon Tool", tool));

    tool = new BorderTool(view());
    palette.add(createToolButton(IMAGES + "BORDDEC", "Border Tool", tool));

    tool = new URLTool(view(), new RectangleFigure());
    palette.add(createToolButton(IMAGES + "URL", "URL Tool", tool));
    palette.setBackground(new Color(192, 192, 192));
  }
  
  //------------------------------------------------------------------------------
  // Modifications to create a floating toolbox :)
   
  /* Returning null here will stop the tool panel from being built as part of the main frame.
   */
  /*protected Panel createWestPanel()
  {
    return null;
  }
  */
/*  private void populateWestPalette(Panel palette) {
    // get the default selection tool
    super.populateWestPanel(palette);

    Tool tool = new TextTool(view(), new TextFigure());
    palette.add(createToolButton(IMAGES + "TEXT", "Text Tool", tool));

    tool = new ConnectedTextTool(view(), new TextFigure());
    palette
        .add(createToolButton(IMAGES + "ATEXT", "Connected Text Tool", tool));

    tool = new CreationTool(view(), new RectangleFigure());
    palette.add(createToolButton(IMAGES + "RECT", "Rectangle Tool", tool));

    tool = new CreationTool(view(), new RoundRectangleFigure());
    palette
        .add(createToolButton(IMAGES + "RRECT", "Round Rectangle Tool", tool));

    tool = new CreationTool(view(), new EllipseFigure());
    palette.add(createToolButton(IMAGES + "ELLIPSE", "Ellipse Tool", tool));

    tool = new CreationTool(view(), new LineFigure());
    palette.add(createToolButton(IMAGES + "LINE", "Line Tool", tool));

    tool = new ConnectionTool(view(), new LineConnection());
    palette.add(createToolButton(IMAGES + "CONN", "Connection Tool", tool));

    tool = new ConnectionTool(view(), new ElbowConnection());
    palette.add(createToolButton(IMAGES + "OCONN", "Elbow Connection Tool",
        tool));

    tool = new ScribbleTool(view());
    palette.add(createToolButton(IMAGES + "SCRIBBL", "Scribble Tool", tool));

    tool = new PolygonTool(view());
    palette.add(createToolButton(IMAGES + "POLYGON", "Polygon Tool", tool));

    tool = new BorderTool(view());
    palette.add(createToolButton(IMAGES + "BORDDEC", "Border Tool", tool));

    tool = new URLTool(view(), new RectangleFigure());
    palette.add(createToolButton(IMAGES + "URL", "URL Tool", tool));
    palette.setBackground(new Color(192, 192, 192));
  }
*/
  protected Panel createSouthPanel()
  {
    Panel split = new Panel();
    split.setLayout(new GridLayout(2, 1));
    split.setBackground(new Color(192, 192, 192));
    return split;
  }

  protected void populateSouthPanel(Panel panel)
  {
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

    button = new CommandButton(
        new BringToFrontCommand("Bring To Front", view()));
    buttons.add(button);

    button = new CommandButton(new SendToBackCommand("Send To Back", view()));
    buttons.add(button);

/*    button = new Button("Help");
    button.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent event)
      {
        showHelp();
      }
    });
    buttons.add(button);
  */
    panel.add(buttons);
    fStatusLabel = new TextField("Status");
    fStatusLabel.setEditable(false);
    fStatusLabel.setBackground(SystemColor.control);
    
    
    Panel dummyContainer = new Panel();
    dummyContainer.setLayout(new GridBagLayout());
    
    GridBagConstraints constraints = new GridBagConstraints();
    constraints.weighty=0.66;
    constraints.weightx=0.9;
    constraints.fill = GridBagConstraints.HORIZONTAL;
    
    dummyContainer.add(fStatusLabel, constraints);
    panel.add(dummyContainer);
  }

  public void showStatus(String s)
  {
    if (fStatusLabel != null)
      fStatusLabel.setText(s);
    else
      getApplication().showStatus(s);
  }

  /**
   * Workaround to get it work without update button
   */
  protected void setSimpleDisplayUpdate()
  {
  }

  protected void setBufferedDisplayUpdate()
  {
  }

  //-- actions -----------------------------------------

  protected void showHelp()
  {
    try
    {
      // gets help file path
      String helpPath = getApplication().getParameter(HELPPATH_PARAMETER);
      if (helpPath != null)
      {
        URL url = getApplication().getURL(helpPath);
        getApplication().popupFrame(url, "Help");
      }
    } catch (IOException e)
    {
      showStatus("Help file not found");
    }
  }

  class NewDrawingCommand extends Command
  {
    TWikiFrame frame;

    public NewDrawingCommand(TWikiFrame frm)
    {
      super("Clear");
      frame = frm;
    }

    public void execute()
    {
      frame.doLoadDrawing(DRAWLOADPATH_PARAMETER);
    }
  }

  class ReloadDrawingCommand extends Command
  {
    TWikiFrame frame;

    public ReloadDrawingCommand(TWikiFrame frm)
    {
      super("Reload");
      frame = frm;
    }

    public void execute()
    {
      frame.doLoadDrawing(DRAWLOADPATH_PARAMETER);
    }
  }

  class SaveDrawingCommand extends Command
  {
    TWikiFrame frame;

    public SaveDrawingCommand(TWikiFrame frm)
    {
      super("Save and Exit");
      frame = frm;
    }

    public void execute()
    {
      Application application = getApplication();
      if(application instanceof TWikiDraw) {
        if (frame.doSaveDrawing()) {
          ( (TWikiDraw) application ).exitApplet();
        }
      }
      else if(application instanceof StandAlone) {
        System.exit(0);
      }      
    }
  }

  class ExitDrawingCommand extends Command
  {
    TWikiFrame frame;

    public ExitDrawingCommand(TWikiFrame frm)
    {
      super("Exit without saving");
      frame = frm;
    }

    public void execute()
    {
      Application application = getApplication();
      if(application instanceof TWikiDraw) {
        ( (TWikiDraw) application ).exitApplet();
      }
      else if(application instanceof StandAlone) {
        System.exit(0);
      }
    }
  }

  public void doLoadDrawing(String name)
  {
    loadDrawing(name);
    view().setBackground(Color.white);
  }

  public boolean doSaveDrawing()
  {
    TWikiDraw app = (TWikiDraw) getApplication();
    boolean savedDraw, savedSvg, savedGif, savedMap;
    savedDraw = savedSvg = savedGif = savedMap = false;

    // set wait cursor
    setCursor(new Cursor(Cursor.WAIT_CURSOR));

    try
    {
      // saves the drawing to the stream of bytes
      ByteArrayOutputStream out = new ByteArrayOutputStream();
      StorableOutput output = new StorableOutput(out);
      // drawing() (class DrawFrame) returns the Drawing element
      // Drawing is a StandardDrawing (extends Drawing
      // and implements CompositeFigures)
      output.writeStorable(drawing());
      output.close();

      String wikiUrl = app.getParameter("wikiurl");

      // gets pathname of the drawing
      String drawingName = app.getParameter(DRAWINGNAME_PARAMETER);
      if (drawingName == null)
        drawingName = "untitled";

      // gets script name
      String savePath = app.getParameter(PAGENAME_PARAMETER);
      debug("SavePath:" + savePath);
      showStatus("SavePath : " + savePath);
      if (savePath == null)
        savePath = "";

      // submit POST command to the server three times:
      // *.draw, *.map and *.gif
      // first upload *.draw file
      showStatus("Saving .draw file " + drawingName+".draw");
      debug("Saving .draw file " + drawingName+".draw");
      if (bPostEnabled)
        savedDraw = app.post(wikiUrl, savePath, "text/plain", drawingName+".draw", out
            .toString(), "TWiki Draw draw file");

      // calculate the minimum size of the gif image
      Dimension d = new Dimension(0, 0); // not this.view().getSize();
      FigureEnumeration k = drawing().figuresReverse();
      while (k.hasMoreElements())
      {
        Figure figure = k.nextFigure();
        Rectangle r = figure.displayBox();
        if (r.x + r.width > d.width)
        {
          d.setSize(r.x + r.width, d.height);
        }
        if (r.y + r.height > d.height)
        {
          d.setSize(d.width, r.y + r.height);
        }
      }

      // gets add border size
      int iBorder = 10;
      String sBorder = getApplication().getParameter(BORDERSIZE_PARAMETER);
      if (sBorder != null)
      {
        iBorder = Integer.valueOf(sBorder).intValue();
        if (iBorder < 0)
        {
          iBorder = 0;
        }
      }

      String map = drawing().getMap();
      String mapPath = drawingName + ".map";
      showStatus("Saving .map file " + mapPath);
      // enclose the map and add editable border. Note that the
      // edit border is added LAST so the earlier AREAs take
      // precedence.
      String area = "<area shape=\"rect\" coords=\"";
      String link = "\" href=\"%BUILDEDITLINK%\" " + "alt=\"Click to edit the image\" title=\"Click to edit the image\"  />\n";
      map = "<map name=\"" + app.getParameter(DRAWINGNAME_PARAMETER) + "\" id=\""+ app.getParameter(DRAWINGNAME_PARAMETER)+" \">" + map + 

      area +
	    "0,0," + (d.width+iBorder) + "," + (iBorder/2) +
	    link +

	    area +
	    "0,0," + iBorder/2 + "," + (d.height+iBorder) +
	    link +

	    area +
	    (d.width+iBorder/2) + ",0," + (d.width+iBorder) + "," +
          (d.height+iBorder) +
	    link + 

	    area +
	    "0," + (d.height+iBorder/2) + "," +
	    (d.width+iBorder) + "," + (d.height+iBorder) +
	    link +

	    "</map>";
      
      savedMap = app.post(wikiUrl, savePath, "text/plain", mapPath, map, "TWiki Draw map file");

      // gets pathname of the GIF image
      String gifPath  = drawingName + ".gif";

      // then create *.gif image and upload file
      showStatus("Saving .gif file " + gifPath);

      // clear the selection so it doesn't appear
      view().clearSelection();

      final Image oImgBuffer = this.view().createImage(d.width + iBorder,
          d.height + iBorder);
      final char[] aChar = convertToGif(oImgBuffer);

      // upload *.gif file
      if (bPostEnabled)
        savedGif = app.post(wikiUrl, savePath, "image/gif", gifPath, String
            .valueOf(aChar, 0, aChar.length), "TWiki Draw GIF file");
    } catch (MalformedURLException e)
    {
      this.setCursor(new Cursor(Cursor.DEFAULT_CURSOR));
      showStatus("Bad Wiki servlet URL: " + e.getMessage());
    } catch (IOException e)
    {
      e.printStackTrace();
      this.setCursor(new Cursor(Cursor.DEFAULT_CURSOR));
      showStatus(e.toString());
    }
    this.setCursor(new Cursor(Cursor.DEFAULT_CURSOR));
    showStatus("Saved .draw " + (savedDraw ? "OK" : "Failed") + " .map "
        + (savedMap ? "OK" : "Failed") + " .gif "
        + (savedGif ? "OK" : "Failed"));
    return savedDraw;
  }

  /** POST can be disabled for testing purposes */
  void enablePost(boolean b)
  {
    bPostEnabled = b;
    if (!bPostEnabled)
      this.setTitle(this.getTitle() + " - POST DISABLED FOR TESTING");
  }

  /** debugging messages */
  public static void debug(String msg)
  {
    System.err.println("TWikiDraw:" + msg);
  }

  /**
   * convert Image to GIF-encoded data, reducing the number of colors if needed.
   * Added by Bertrand Delacretaz
   */
  private char[] convertToGif(Image oImgBuffer) throws IOException
  {
    debug("converting data to GIF...");
    Graphics oGrf = oImgBuffer.getGraphics();
    this.view().enableGuides(false);
    this.view().drawAll(oGrf);

    // test gif image:
    //TestFrame tf = new TestFrame( "tt2: " + oImgBuffer.toString() );
    //tf.setSize(new Dimension(d.width+30, d.height+30));
    //tf.setImage(oImgBuffer);
    //tf.show();

    ByteArrayOutputStream oOut = null;

    try
    {
      oOut = new ByteArrayOutputStream();
      new GifEncoder(oImgBuffer, oOut).encode();
    } catch (IOException ioe)
    {
      // GifEncoder throws IOException when GIF contains too many colors
      // if this happens, filter image to reduce number of colors
      debug("GIF uses too many colors, reducing to 216 colors...");
      //TODO: final FilteredImageSource filter = new
      // FilteredImageSource(oImgBuffer.getSource(),new Web216ColorsFilter());
      //	    oOut = new ByteArrayOutputStream();
      //    new GifEncoder(filter,oOut).encode (); 
      debug("Color reduction successful.");
    }

    byte[] aByte = oOut.toByteArray();
    int size = oOut.size();
    char[] aChar = new char[size];
    for (int i = 0; i < size; i++)
    {
      aChar[i] = (char) aByte[i];
    }
    debug("conversion to GIF successful.");
    return aChar;
  }
}