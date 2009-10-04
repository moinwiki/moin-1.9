/*
 * @(#)JavaDrawApp.java
 *
 * Project:		JHotdraw - a GUI framework for technical drawings
 *				http://www.jhotdraw.org
 *				http://jhotdraw.sourceforge.net
 * Copyright:	© by the original author(s) and all contributors
 * License:		Lesser GNU Public License (LGPL)
 *				http://www.opensource.org/licenses/lgpl-license.html
 */

package com.wombatinvasion.pmwikidraw;

import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.GraphicsEnvironment;
import java.awt.Image;
import java.awt.MenuShortcut;
import java.awt.Point;
import java.awt.Rectangle;
import java.awt.Stroke;
import java.awt.event.KeyAdapter;
import java.awt.event.KeyEvent;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.awt.image.FilteredImageSource;
import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.ObjectInput;
import java.io.ObjectInputStream;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLConnection;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.ResourceBundle;
import java.util.StringTokenizer;
import java.util.Vector;

import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JOptionPane;
import javax.swing.JToolBar;

import org.jhotdraw.application.DrawApplication;
import org.jhotdraw.contrib.CustomToolBar;
import org.jhotdraw.contrib.DiamondFigure;
import org.jhotdraw.contrib.PolygonTool;
import org.jhotdraw.contrib.SplitConnectionTool;
import org.jhotdraw.contrib.TextAreaFigure;
import org.jhotdraw.contrib.TextAreaTool;
import org.jhotdraw.contrib.TriangleFigure;
import org.jhotdraw.contrib.dnd.DragNDropTool;
import org.jhotdraw.contrib.dnd.JHDDropTargetListener;
import org.jhotdraw.figures.BorderTool;
import org.jhotdraw.figures.ConnectedTextTool;
import org.jhotdraw.figures.ElbowConnection;
import org.jhotdraw.figures.EllipseFigure;
import org.jhotdraw.figures.GroupCommand;
import org.jhotdraw.figures.InsertImageCommand;
import org.jhotdraw.figures.LineConnection;
import org.jhotdraw.figures.LineFigure;
import org.jhotdraw.figures.PolyLineFigure;
import org.jhotdraw.figures.RectangleFigure;
import org.jhotdraw.figures.RoundRectangleFigure;
import org.jhotdraw.figures.ScribbleTool;
import org.jhotdraw.figures.TextFigure;
import org.jhotdraw.figures.TextTool;
import org.jhotdraw.figures.UngroupCommand;
import org.jhotdraw.framework.Drawing;
import org.jhotdraw.framework.DrawingView;
import org.jhotdraw.framework.FigureAttributeConstant;
import org.jhotdraw.framework.FigureSelectionListener;
import org.jhotdraw.framework.JHotDrawRuntimeException;
import org.jhotdraw.framework.Painter;
import org.jhotdraw.framework.PointConstrainer;
import org.jhotdraw.framework.Tool;
import org.jhotdraw.samples.javadraw.URLTool;
import org.jhotdraw.standard.AbstractCommand;
import org.jhotdraw.standard.AlignCommand;
import org.jhotdraw.standard.BringToFrontCommand;
import org.jhotdraw.standard.ChangeAttributeCommand;
import org.jhotdraw.standard.ConnectionTool;
import org.jhotdraw.standard.CopyCommand;
import org.jhotdraw.standard.CreationTool;
import org.jhotdraw.standard.CutCommand;
import org.jhotdraw.standard.DeleteCommand;
import org.jhotdraw.standard.DuplicateCommand;
import org.jhotdraw.standard.GridConstrainer;
import org.jhotdraw.standard.PasteCommand;
import org.jhotdraw.standard.SelectAllCommand;
import org.jhotdraw.standard.SelectionTool;
import org.jhotdraw.standard.SendToBackCommand;
import org.jhotdraw.standard.ToggleGridCommand;
import org.jhotdraw.standard.ToolButton;
import org.jhotdraw.util.ColorMap;
import org.jhotdraw.util.Command;
import org.jhotdraw.util.CommandMenu;
import org.jhotdraw.util.PaletteButton;
import org.jhotdraw.util.PaletteListener;
import org.jhotdraw.util.RedoCommand;
import org.jhotdraw.util.StorableInput;
import org.jhotdraw.util.UndoCommand;
import org.jhotdraw.util.UndoableCommand;
import org.jhotdraw.util.UndoableTool;

import Acme.JPM.Encoders.GifEncoder;

import com.eteks.filter.Web216ColorsFilter;
import com.wombatinvasion.pmwikidraw.gui.SymbolPackageContainer;

/**
 * @version <$CURRENT_VERSION$>
 */
public  class PmWikiDrawFrame extends DrawApplication {

	private static String         fgSampleImagesPath = "/org/jhotdraw/samples/javadraw/sampleimages";
	private static String         fgSampleImagesResourcePath = fgSampleImagesPath + "/";
	private PmWikiSource 		  _pmwikisource;
	private Drawing				  fDrawing = null;
	private final ResourceBundle  menuStrings;
	private final ResourceBundle  toolStrings;
	private CustomToolBar 		  toolBar;
	
	/**
	 * Expose constructor for benefit of subclasses.
	 *
	 * @param title The window title for this application's frame.
	 */
	public PmWikiDrawFrame(PmWikiSource pmwikisource) {
		super("PmWikiDraw - "+ pmwikisource.getPmWikiParameter(PmWikiSource.PARAMETER_DRAWING));
		_pmwikisource = pmwikisource;
		Locale locale = Locale.getDefault();
		//Locale locale = new Locale("de", "DE");
//		Locale locale = new Locale("fr", "FR");
		menuStrings = ResourceBundle.getBundle("Menus",locale);		
		toolStrings = ResourceBundle.getBundle("Tools",locale);
		addKeyListener(new KeyAdapter() {
			public void keyPressed(KeyEvent e)
			{
				int code = e.getKeyCode();
				//System.out.println(code);
				// modify Ctrl combinations
				if( ( e.getModifiers() & KeyEvent.CTRL_MASK) == KeyEvent.CTRL_MASK) {
				  switch(code) {
			    case  KeyEvent.VK_Q:
            performExitAndDiscard();
						break;
          case  KeyEvent.VK_S:
            performSave();
            break;
				  default:
							super.keyPressed(e);
				  	  break;
				  }
				}
        else if( ( e.getModifiers() & KeyEvent.ALT_MASK) == KeyEvent.ALT_MASK) {
          switch(code) {
          case KeyEvent.VK_X:
            performSaveAndExit();
            break;
          default:
            super.keyPressed(e);
            break;
          }
        }
        else {
					super.keyPressed(e);
				}
			}

		}); 
	}

  private void performSaveAndExit()
  {
    int saveResult = _pmwikisource.saveDrawing(fDrawing);
    if(saveResult == PmWikiSource.SAVE_SUCCESS) { 
      endApp(true);
    } 
    else if(saveResult == PmWikiSource.SAVE_FAILURE_PASSWORD) {
          JOptionPane.showMessageDialog(PmWikiDrawFrame.this, "I'm sorry, but your password is not recognised.", "Password Failure", JOptionPane.WARNING_MESSAGE);
    }
    else if(saveResult == PmWikiSource.SAVE_FAILURE_CONCURRENTMODIFICATION) {
      JOptionPane.showMessageDialog(PmWikiDrawFrame.this, "It appears that someone has modified the drawing whilst you've been working on it.\nIf you save again you will lose the *other* user's changes.(But yours will remain!)", "Concurrent modification!", JOptionPane.WARNING_MESSAGE);
    }
    else {
      System.err.println("Hmmm invalid response from the drwaing save, weird!");
    }
  }     

	/**
	 * Factory method which create a new instance of this
	 * application.
	 *
	 * @return	newly created application
	 */
	protected DrawApplication createApplication() {
		return new PmWikiDrawFrame(_pmwikisource);
	}
	
	protected DrawingView createDrawingView(Drawing newDrawing) {
		Dimension d = getDrawingViewSize();
//		DrawingView newDrawingView = new ZoomDrawingView(this, d.width, d.height);
//		DrawingView newDrawingView = new StandardDrawingView(this, d.width, d.height);
		PmWikiDrawingView newDrawingView = new PmWikiDrawingView(this, d.width, d.height);
		newDrawingView.setQualityMode(true);
		newDrawingView.setDrawing(newDrawing);
		// notify listeners about created view when the view is added to the desktop
		//fireViewCreatedEvent(newDrawingView);
		newDrawingView.setBackground(Color.white);
		newDrawingView.setConstrainer(new GridConstrainer(10, 10));
		newDrawingView.addFigureSelectionListener(new FigureSelectionListener(){
			/* (non-Javadoc)
			 * @see org.jhotdraw.framework.FigureSelectionListener#figureSelectionChanged(org.jhotdraw.framework.DrawingView)
			 */
			public void figureSelectionChanged(DrawingView view) {
			  
			  if(view().selectionCount() > 0) {
					toolBar.switchToEditTools();
					toolBar.activateTools();
				} 
				else {
					toolBar.switchToStandardTools();
					toolBar.activateTools();
				}
			}
			});
		JHDDropTargetListener targetListener = new JHDDropTargetListener(this, newDrawingView);
		return newDrawingView;
	}

	//-- application life cycle --------------------------------------------

	public void destroy() {
		super.destroy();
	}

	//-- DrawApplication overrides -----------------------------------------

	protected void createTools(JToolBar palette) {
		toolBar = (CustomToolBar)palette;
		toolBar.switchToStandardTools();
		super.createTools(palette);

//		Tool tool = new ZoomTool(this);
//		palette.add(createToolButton(IMAGES + "ZOOM", "Zoom Tool", tool));

		Tool tool = new UndoableTool(new TextTool(this, new TextFigure()));
		palette.add(createToolButton(IMAGES + "TEXT", toolStrings.getString("text"), tool));

		tool = new UndoableTool(new ConnectedTextTool(this, new TextFigure()));
		palette.add(createToolButton(IMAGES + "ATEXT", toolStrings.getString("connectedText"), tool));

		tool = new TextAreaTool(this, new TextAreaFigure());
		palette.add(createToolButton(IMAGES + "TEXTAREA", toolStrings.getString("textArea"), tool));

		tool = new URLTool(this);
		palette.add(createToolButton(IMAGES + "URL", toolStrings.getString("url"), tool));

		
		tool = new UndoableTool(new CreationTool(this, new RectangleFigure()));
		palette.add(createToolButton(IMAGES + "RECT", toolStrings.getString("rectangle"), tool));

		tool = new UndoableTool(new CreationTool(this, new RoundRectangleFigure()));
		palette.add(createToolButton(IMAGES + "RRECT", toolStrings.getString("roundRectangle"), tool));

		tool = new UndoableTool(new CreationTool(this, new EllipseFigure()));
		palette.add(createToolButton(IMAGES + "ELLIPSE", toolStrings.getString("ellipse"), tool));

		tool = new UndoableTool(new PolygonTool(this));
		palette.add(createToolButton(IMAGES + "POLYGON", toolStrings.getString("polygon"), tool));

		tool = new UndoableTool(new CreationTool(this, new TriangleFigure()));
		palette.add(createToolButton(IMAGES + "TRIANGLE", toolStrings.getString("triangle"), tool));

		tool = new UndoableTool(new CreationTool(this, new DiamondFigure()));
		palette.add(createToolButton(IMAGES + "DIAMOND", toolStrings.getString("diamond"), tool));

		tool = new UndoableTool(new CreationTool(this, new LineFigure()));
		palette.add(createToolButton(IMAGES + "LINE", toolStrings.getString("line"), tool));

		tool = new UndoableTool(new PmWikiScribbleTool(this));
		palette.add(createToolButton(IMAGES + "ASCRIBBL", toolStrings.getString("assistedScribble"), tool));

		tool = new UndoableTool(new PmWikiScribbleTool(this, true));
		palette.add(createToolButton(IMAGES + "SCRIBBL", toolStrings.getString("scribble"), tool));

		tool = new UndoableTool(new ConnectionTool(this, new LineConnection()));
		palette.add(createToolButton(IMAGES + "CONN", toolStrings.getString("connection"), tool));

		tool = new UndoableTool(new ConnectionTool(this, new ElbowConnection()));
		palette.add(createToolButton(IMAGES + "OCONN", toolStrings.getString("elbowConnection"), tool));

//		tool = new UndoableTool(new ConnectionTool(this, new AttributeConnectorFigure(new ArcLine())));
	//	palette.add(createToolButton(IMAGES + "CCONN", "Quad-Curved Connection Tool", tool));
	//	tool = new UndoableTool(new ConnectionTool(this, new ArcLine()));
		//palette.add(createToolButton(IMAGES + "CCONN", "Quad-Curved Connection Tool", tool));

		LineConnection lineConnection = new LineConnection();
		lineConnection.setStartDecoration(null);
		
		tool = new UndoableTool(new SplitConnectionTool(this, lineConnection));
		palette.add(createToolButton(IMAGES + "OCONN", toolStrings.getString("splitConnection"), tool));
		
		tool = new DragNDropTool(this);
		//palette.add(createToolButton(IMAGES + "SELECT", "DnD", tool));
		/*
		Component button = new JButton("Hello World (JButton!)");
		tool = new CreationTool(this, new ComponentFigure(button));
		palette.add(createToolButton(IMAGES + "RECT", toolStrings.getString("component"), tool));

		GraphicalCompositeFigure fig = new GraphicalCompositeFigure();
		fig.setLayouter(new SimpleLayouter(fig));
		tool = new CreationTool(this, fig);
		palette.add(createToolButton(IMAGES + "RECT", toolStrings.getString("container"), tool));

		tool = new CompositeFigureCreationTool(this, new RectangleFigure());
		palette.add(createToolButton(IMAGES + "RECT", toolStrings.getString("nested"), tool));

		tool = new HTMLTextAreaTool(this, new HTMLTextAreaFigure());
		palette.add(createToolButton(IMAGES + "TEXTAREA", "HTML TextArea Tool", tool));
		tool = new UndoableTool(new BorderTool(this));
		palette.add(createToolButton(IMAGES + "BORDDEC", toolStrings.getString("border"), tool));
*/
    palette.add( new PaletteCommandButton( (PaletteListener)this, IMAGES, menuStrings.getString("attributesFillColor"), FigureAttributeConstant.FILL_COLOR, this ) ) ;
    palette.add( new PaletteCommandButton( (PaletteListener)this, IMAGES, menuStrings.getString("attributesPenColor"),  FigureAttributeConstant.FRAME_COLOR, this ) ) ;
    palette.add( new PaletteCommandButton( (PaletteListener)this, IMAGES, menuStrings.getString("attributesTextColor"), FigureAttributeConstant.TEXT_COLOR, this ) ) ;

    /*palette.add( new PaletteCommandButton( (PaletteListener)this, IMAGES, menuStrings.getString("attributesFillColor"), new UndoableCommand(new ColorPaletteChangeAttributeCommand("Select...", FigureAttributeConstant.FILL_COLOR, this))) ) ;
    palette.add( new PaletteCommandButton( (PaletteListener)this, IMAGES, menuStrings.getString("attributesPenColor"), new UndoableCommand(new ColorPaletteChangeAttributeCommand("Select...", FigureAttributeConstant.FRAME_COLOR, this))) ) ;
    palette.add( new PaletteCommandButton( (PaletteListener)this, IMAGES, menuStrings.getString("attributesTextColor"), new UndoableCommand(new ColorPaletteChangeAttributeCommand("Select...", FigureAttributeConstant.TEXT_COLOR, this))) ) ;
    */
		toolBar.switchToEditTools();
		
		palette.add(createCommandButton(IMAGES+"CUT", menuStrings.getString("editCut"), new UndoableCommand(new CutCommand(menuStrings.getString("editCut"), this))));
		palette.add(createCommandButton(IMAGES+"COPY", menuStrings.getString("editCopy"), new UndoableCommand(new CopyCommand(menuStrings.getString("editCopy"), this))));
		palette.add(createCommandButton(IMAGES+"PASTE", menuStrings.getString("editPaste"), new UndoableCommand(new PasteCommand(menuStrings.getString("editPaste"), this))));
		palette.add(createCommandButton(IMAGES+"DUP", menuStrings.getString("editDuplicate"), new UndoableCommand(new DuplicateCommand(menuStrings.getString("editDuplicate"), this))));
		palette.add(createCommandButton(IMAGES+"DEL", menuStrings.getString("editDelete"), new UndoableCommand(new DeleteCommand(menuStrings.getString("editDelete"), this))));
/*		palette.add( new PaletteCommandButton( (PaletteListener)this, IMAGES, menuStrings.getString("attributesFillColor"), new UndoableCommand(new ColorPaletteChangeAttributeCommand("Select...", FigureAttributeConstant.FILL_COLOR, this))) ) ;
		palette.add( new PaletteCommandButton( (PaletteListener)this, IMAGES, menuStrings.getString("attributesPenColor"), new UndoableCommand(new ColorPaletteChangeAttributeCommand("Select...", FigureAttributeConstant.FRAME_COLOR, this))) ) ;
		palette.add( new PaletteCommandButton( (PaletteListener)this, IMAGES, menuStrings.getString("attributesTextColor"), new UndoableCommand(new ColorPaletteChangeAttributeCommand("Select...", FigureAttributeConstant.TEXT_COLOR, this))) ) ;
*/    
    palette.add( new PaletteCommandButton( (PaletteListener)this, IMAGES, menuStrings.getString("attributesFillColor"), FigureAttributeConstant.FILL_COLOR, this ) ) ;
    palette.add( new PaletteCommandButton( (PaletteListener)this, IMAGES, menuStrings.getString("attributesPenColor"),  FigureAttributeConstant.FRAME_COLOR, this ) ) ;
    palette.add( new PaletteCommandButton( (PaletteListener)this, IMAGES, menuStrings.getString("attributesTextColor"), FigureAttributeConstant.TEXT_COLOR, this ) ) ;

		toolBar.switchToStandardTools();
		toolBar.activateTools();
}
//	protected Tool createSelectionTool() {
	//	return new MySelectionTool(this);
	//}

	protected void createMenus(JMenuBar mb) {
		addMenuIfPossible(mb, createFileMenu());
		addMenuIfPossible(mb, createEditMenu());
		addMenuIfPossible(mb, createAlignmentMenu());
		addMenuIfPossible(mb, createAttributesMenu());
		addMenuIfPossible(mb, createImagesMenu()); 
		addMenuIfPossible(mb, createSymbolsMenu());
	}
	//------------------------------------------------------------------------------
  /**
   * @return
   */
  private JMenu createSymbolsMenu()
  {
  	final String imagesPath = _pmwikisource.getPmWikiParameter(PmWikiSource.PARAMETER_RESOURCESURL)+"/symbols/";
  	CommandMenu rootMenu = new CommandMenu(menuStrings.getString("symbolsMenu"));
	    List symbols = new Vector();
        try {
    		URL url  = new URL(imagesPath+"symbols");
			URLConnection urlC = url.openConnection();
			// if no local file name specified
			InputStream is = url.openStream();
			if (is == null) {
				throw new JHotDrawRuntimeException("Could not locate symbol index: " + url.getFile());
			}
		    BufferedReader in = new BufferedReader(new InputStreamReader(is));
		    String line = in.readLine();
		    line = line.trim();
		    while(line!=null) {
		    	if(!line.startsWith("#") && !line.equals("")) { //Ignore comments.
		    		symbols.add(line);
		    	}
		      line = in.readLine();
		      if(line!=null) 
		      	line = line.trim();
		    }
			is.close();
		} catch (IOException e1) {
			System.err.println("It seems that the administrator has disabled symbol insertions on this PmWiki, sorry.");
		}
		if(symbols.size()>0) {
			for (int i = 0; i < symbols.size(); i++) {
				final String name = (String) symbols.get(i);
				rootMenu.add( new AbstractCommand(name, this, true) {
					public void execute() {
						SymbolPackageContainer symbol = new SymbolPackageContainer(imagesPath+name+".jar");
					}
				});
			}
			return rootMenu;
		}
		else {
			return null;
		}
	}

  //------------------------------------------------------------------------------
	/**
	 * Creates the edit menu. Clients override this
	 * method to add additional menu items.
	 */
	protected JMenu createEditMenu() {
		CommandMenu menu = new CommandMenu(menuStrings.getString("editMenu"));
		menu.add(new UndoCommand(menuStrings.getString("editUndo"), this));
		menu.add(new RedoCommand(menuStrings.getString("editRedo"), this));
		menu.addSeparator();
		menu.add(new UndoableCommand(
			new SelectAllCommand(menuStrings.getString("editSelectAll"), this)), new MenuShortcut(menuStrings.getString("editSelectAll").charAt(0)));
		menu.addSeparator();
		menu.add(new UndoableCommand(
			new CutCommand(menuStrings.getString("editCut"), this)), new MenuShortcut(menuStrings.getString("editCutShortcut").charAt(0)));
		menu.add(new CopyCommand(menuStrings.getString("editCopy"), this), new MenuShortcut(menuStrings.getString("editCopyShortcut").charAt(0)));
		menu.add(new UndoableCommand(
			new PasteCommand(menuStrings.getString("editPaste"), this)), new MenuShortcut(menuStrings.getString("editPasteShortcut").charAt(0)));
		menu.addSeparator();
		menu.add(new UndoableCommand(
			new DuplicateCommand(menuStrings.getString("editDuplicate"), this)), new MenuShortcut(menuStrings.getString("editDuplicateShortcut").charAt(0)));
		menu.add(new UndoableCommand(new DeleteCommand(menuStrings.getString("editDelete"), this)));
		menu.addSeparator();
		menu.add(new UndoableCommand(new GroupCommand(menuStrings.getString("editGroup"), this)));
		menu.add(new UndoableCommand(new UngroupCommand(menuStrings.getString("editUngroup"), this)));
		menu.addSeparator();
		menu.add(new UndoableCommand(new SendToBackCommand(menuStrings.getString("editSendToBack"), this)));
		menu.add(new UndoableCommand(new BringToFrontCommand(menuStrings.getString("editBringToFront"), this)));
		return menu;
	}
	/**
	 * Creates the alignment menu. Clients override this
	 * method to add additional menu items.
	 */
	protected JMenu createAlignmentMenu() {
		CommandMenu menu = new CommandMenu(menuStrings.getString("alignMenu"));
		menu.addCheckItem(new ToggleGridCommand(menuStrings.getString("alignSnap"), this, new Point(10,10)), (view().getConstrainer()!=null) );

		menu.addSeparator();
		menu.add(new UndoableCommand(
			new AlignCommand(AlignCommand.Alignment.LEFTS, this)));
		menu.add(new UndoableCommand(
			new AlignCommand(AlignCommand.Alignment.CENTERS, this)));
		menu.add(new UndoableCommand(
			new AlignCommand(AlignCommand.Alignment.RIGHTS, this)));
		menu.addSeparator();
		menu.add(new UndoableCommand(
			new AlignCommand(AlignCommand.Alignment.TOPS, this)));
		menu.add(new UndoableCommand(
			new AlignCommand(AlignCommand.Alignment.MIDDLES, this)));
		menu.add(new UndoableCommand(
			new AlignCommand(AlignCommand.Alignment.BOTTOMS, this)));
		return menu;
	}
	
	/**
	 * Creates the attributes menu and its submenus. Clients override this
	 * method to add additional menu items.
	 */
	protected JMenu createAttributesMenu() {
		JMenu menu = new JMenu(menuStrings.getString("attributesMenu"));
		menu.add(createColorMenu(menuStrings.getString("attributesFillColor"), FigureAttributeConstant.FILL_COLOR));
		menu.add(createColorMenu(menuStrings.getString("attributesPenColor"), FigureAttributeConstant.FRAME_COLOR));
		menu.add(createLineWidthMenu());
		menu.add(createLineStyleMenu());
		menu.add(createArrowMenu());
		menu.addSeparator();
		menu.add(createFontMenu());
		menu.add(createFontSizeMenu());
		menu.add(createFontStyleMenu());
		menu.add(createColorMenu(menuStrings.getString("attributesTextColor"), FigureAttributeConstant.TEXT_COLOR));
		return menu;
	}	
	
	/**
	 * Creates the color menu.
	 */
	protected JMenu createColorMenu(String title, FigureAttributeConstant attribute) {
		CommandMenu menu = new CommandMenu(title);
		for (int i=0; i<ColorMap.size(); i++)
			menu.add(
				new UndoableCommand(
					new ChangeAttributeCommand(
						ColorMap.name(i),
						attribute,
						ColorMap.color(i),
						this
					)
				)
			);
		
		menu.add(new UndoableCommand(new ColorPaletteChangeAttributeCommand("Select...", attribute, this)));
		return menu;
	}	
	/**
	 * Creates the arrows menu.
	 */
	protected JMenu createArrowMenu() {
		FigureAttributeConstant arrowMode = FigureAttributeConstant.ARROW_MODE;
		CommandMenu menu = new CommandMenu(menuStrings.getString("attributesArrow"));
		menu.add(new UndoableCommand(
			new ChangeAttributeCommand(menuStrings.getString("attributesArrowNone"), arrowMode, new Integer(PolyLineFigure.ARROW_TIP_NONE), this)));
		menu.add(new UndoableCommand(
			new ChangeAttributeCommand(menuStrings.getString("attributesArrowStart"), arrowMode, new Integer(PolyLineFigure.ARROW_TIP_START), this)));
		menu.add(new UndoableCommand(
			new ChangeAttributeCommand(menuStrings.getString("attributesArrowEnd"), arrowMode, new Integer(PolyLineFigure.ARROW_TIP_END), this)));
		menu.add(new UndoableCommand(
			new ChangeAttributeCommand(menuStrings.getString("attributesArrowBoth"), arrowMode, new Integer(PolyLineFigure.ARROW_TIP_BOTH), this)));
		return menu;
	}	
	/**
	 * Creates the font style menu with entries (Plain, Italic, Bold).
	 */
	protected JMenu createFontStyleMenu() {
		FigureAttributeConstant fontStyle = FigureAttributeConstant.FONT_STYLE;
		CommandMenu menu = new CommandMenu(menuStrings.getString("attributesFontStyle"));
		menu.add(new UndoableCommand(
			new ChangeAttributeCommand(menuStrings.getString("attributesFontStylePlain"), fontStyle, new Integer(Font.PLAIN), this)));
		menu.add(new UndoableCommand(
			new ChangeAttributeCommand(menuStrings.getString("attributesFontStyleItalic"), fontStyle, new Integer(Font.ITALIC), this)));
		menu.add(new UndoableCommand(
			new ChangeAttributeCommand(menuStrings.getString("attributesFontStyleBold"), fontStyle, new Integer(Font.BOLD), this)));
		return menu;
	}
	/**
	 * Creates the font size menu.
	 */
	protected JMenu createFontSizeMenu() {
		CommandMenu menu = new CommandMenu(menuStrings.getString("attributesFontSize"));
		int sizes[] = { 9, 10, 12, 14, 18, 24, 36, 48, 72 };
		for (int i = 0; i < sizes.length; i++) {
		   menu.add(
				new UndoableCommand(
					new ChangeAttributeCommand(
						Integer.toString(sizes[i]),
						FigureAttributeConstant.FONT_SIZE,
						new Integer(sizes[i]),
						this
					)
				)
			);
		}
		return menu;
	}

	
	protected JMenu createLineWidthMenu() {
	  CommandMenu menu = new CommandMenu(menuStrings.getString("attributesPenWidth"));
	  menu.add(new UndoableCommand(new ChangeAttributeCommand("1",    FigureAttributeConstant.LINE_WIDTH, new Double(1), this)));
	  menu.add(new UndoableCommand(new ChangeAttributeCommand("1.25", FigureAttributeConstant.LINE_WIDTH, new Double(1.25), this)));
	  menu.add(new UndoableCommand(new ChangeAttributeCommand("1.5",  FigureAttributeConstant.LINE_WIDTH, new Double(1.5), this)));
	  menu.add(new UndoableCommand(new ChangeAttributeCommand("2",    FigureAttributeConstant.LINE_WIDTH, new Double(2), this)));
	  menu.add(new UndoableCommand(new ChangeAttributeCommand("3",    FigureAttributeConstant.LINE_WIDTH, new Double(3), this)));
	  menu.add(new UndoableCommand(new ChangeAttributeCommand("4",    FigureAttributeConstant.LINE_WIDTH, new Double(4), this)));
	  return menu;
	}
	
	
	protected JMenu createLineStyleMenu() {
	  CommandMenu menu = new CommandMenu(menuStrings.getString("attributesPenStyle"));
	  List penStyles = PmWikiLineStyles.getLineStyles();
	  if(penStyles!=null && penStyles.size()>0) {
	    for(int i=0;i<penStyles.size();i++) {
	  	  menu.add(new UndoableCommand(new ChangeAttributeCommand(menuStrings.getString(((PmWikiLineStyles)penStyles.get(i)).getName()),    FigureAttributeConstant.LINE_STYLE, new Integer(((PmWikiLineStyles)penStyles.get(i)).getId()), this)));
	    }
	  }
	  return menu;
	}
	
	
	/**
	 * Creates the fonts menus. It installs all available fonts
	 * supported by the toolkit implementation.
	 */
	protected JMenu createFontMenu() {
		CommandMenu menu = new CommandMenu(menuStrings.getString("attributesFont"));
		String fonts[] = GraphicsEnvironment.getLocalGraphicsEnvironment().getAvailableFontFamilyNames();
		for (int i = 0; i < fonts.length; i++) {
			menu.add(new UndoableCommand(
				new ChangeAttributeCommand(fonts[i], FigureAttributeConstant.FONT_NAME, fonts[i],  this)));
		}
		return menu;
	}	
	
  /**
	 * Creates the file menu. Clients override this
	 * method to add additional menu items.
	 */
	protected JMenu createFileMenu() {
		CommandMenu menu = new CommandMenu(menuStrings.getString("drawingMenu"));
    Command cmd = new AbstractCommand(menuStrings.getString("drawingAbout"), this, true) {
      /* (non-Javadoc)
       * @see org.jhotdraw.standard.AbstractCommand#execute()
       */
      public void execute()
      {
        JOptionPane.showMessageDialog(PmWikiDrawFrame.this, "PmWikiDraw Version: "+PmWikiDraw.VERSION+"\nDrawing version: "+PmWikiDrawing.VERSION, "About PmWikiDraw", JOptionPane.INFORMATION_MESSAGE);
      }
    };
    menu.add(cmd);
    
		cmd = new AbstractCommand(menuStrings.getString("drawingClear"), this, true) {
			public void execute() {
			  if(fDrawing != null) {
				  fDrawing.release();
				  initDrawing();
			  }
			}
		};
		menu.add(cmd, new MenuShortcut(menuStrings.getString("drawingClearShortcut").charAt(0)));
		
		cmd = new AbstractCommand(menuStrings.getString("drawingRevert"), this, true) {
			public void execute() {
			  if(fDrawing != null) {
				  initDrawing();
			  }
			  loadDrawing(PmWikiSource.PARAMETER_DRAWINGLOADPATH);
			}
		};
		menu.add(cmd, new MenuShortcut(menuStrings.getString("drawingRevertShortcut").charAt(0)));
		menu.addSeparator();

		cmd = new AbstractCommand(menuStrings.getString("drawingPrint"), this, true) {
			public void execute() {
				print();
			}
		};
		menu.add(cmd, new MenuShortcut(menuStrings.getString("drawingPrintShortcut").charAt(0)));
		menu.addSeparator();
		menu.addCheckItem(new ToggleQualityCommand(menuStrings.getString("drawingHighQuality"), this), ((PmWikiDrawingView)view()).getQualityMode());
		menu.addSeparator();
		cmd = new AbstractCommand(menuStrings.getString("drawingSave"), this, true) {
			public void execute() {
        performSave();
			}
		};
		menu.add(cmd, new MenuShortcut(menuStrings.getString("drawingSaveShortcut").charAt(0)));

		menu.addSeparator();

		cmd = new AbstractCommand(menuStrings.getString("drawingSaveExit"), this, true) {
			public void execute() {
        performSaveAndExit();
			}
		};
		
		menu.add(cmd, new MenuShortcut(menuStrings.getString("drawingSaveExitShortcut").charAt(0)));

		cmd = new AbstractCommand(menuStrings.getString("drawingExitDiscard"), this, true) {
			public void execute() {
        performExitAndDiscard();
			}
		};
		menu.add(cmd);
		return menu;
	}
 private void performExitAndDiscard() {
   if( JOptionPane.showConfirmDialog(null, "Are you sure you want to discard this drawing?","Discard and exit", JOptionPane.YES_NO_OPTION, JOptionPane.WARNING_MESSAGE) == JOptionPane.YES_OPTION )
   {
    endApp(false);
   }
 }
  private void performSave()
  {
    int saveResult = _pmwikisource.saveDrawing(fDrawing);
    if(saveResult == PmWikiSource.SAVE_SUCCESS) {
      showStatus("Saved drawing...");
    } 
    else if(saveResult == PmWikiSource.SAVE_FAILURE_PASSWORD) {
          JOptionPane.showMessageDialog(this, "I'm sorry, but your password is not recognised.", "Password Failure", JOptionPane.WARNING_MESSAGE);
    }
    else if(saveResult == PmWikiSource.SAVE_FAILURE_CONCURRENTMODIFICATION) {
      JOptionPane.showMessageDialog(this, "It appears that someone has modified the drawing whilst you've been working on it.\nIf you save again you will lose the *other* user's changes.(But yours will remain!)", "Concurrent modification!", JOptionPane.WARNING_MESSAGE);
    }
    else {
      System.err.println("Hmmm invalid response from the drwaing save, weird!");
    }
  }
	/* (non-Javadoc)
   * @see org.jhotdraw.application.DrawApplication#endApp()
   */
  protected void endApp(boolean saved)
  {
    if(closeQuery() == true) {
      _pmwikisource.exit(saved);
    }
  }
  


	protected JMenu createImagesMenu() {
		
		CommandMenu rootMenu = new CommandMenu(menuStrings.getString("imagesMenu"));
		final String imagesPath = _pmwikisource.getPmWikiParameter(PmWikiSource.PARAMETER_RESOURCESURL)+"/images/";
	    List images = new Vector();
        try {
    		URL url  = new URL(imagesPath+"images");
			URLConnection urlC = url.openConnection();
			// if no local file name specified
			InputStream is = url.openStream();
			if (is == null) {
				throw new JHotDrawRuntimeException("Could not locate image index: " + url.getFile());
			}
		    BufferedReader in = new BufferedReader(new InputStreamReader(is));
		    String line = in.readLine();
		    line = line.trim();
		    while(line!=null) {
		    	if(!line.startsWith("#") && !line.equals("")) { //Ignore comments.
		    		images.add(line);
		    	}
		      line = in.readLine();
		      if(line!=null) 
		      	line = line.trim();
		    }
			is.close();
		} catch (IOException e1) {
			System.err.println("It seems that the administrator has disabled image insertions on this PmWiki, sorry.");
		}
		if(images.size()>0) {
			HashMap menus = new HashMap();
			for (int i = 0; i < images.size(); i++) {
				String name = (String) images.get(i);

				// Replace any back slashes with forward slashes. 
				name = name.replace('\\', '/');

				// Replace spaces in path names with %20s (Keeping the original for the menu display)
				StringBuffer encodedName = new StringBuffer("");
				StringTokenizer encodingTokenizer = new StringTokenizer(name, " ");
				if(encodingTokenizer.hasMoreElements()) {
					while(encodingTokenizer.hasMoreElements()) {
						String token = (String)encodingTokenizer.nextElement();
						encodedName.append(token);
						if(encodingTokenizer.hasMoreElements())
							encodedName.append("%20"); 
					}
				}
				else {
					encodedName = new StringBuffer(name);
				}
				
				
				String path = imagesPath+encodedName;
				if(name.indexOf("/")>=0 )  {
					StringTokenizer pathTokenizer = new StringTokenizer(name, "/");
					String token = null;

					int depth =0;
					CommandMenu currentMenu = rootMenu;
					StringBuffer pathHistory = new StringBuffer("");
					while(pathTokenizer.hasMoreElements()) {
						token = (String)pathTokenizer.nextElement();
						token = token.replace('_',' ');
						if(!pathTokenizer.hasMoreElements()) {
							// Handle the menu item itself
							currentMenu.add(new UndoableCommand(new InsertImageCommand(token, path, this, _pmwikisource.getPmWikiParameter(PmWikiSource.PARAMETER_RESOURCESURL))));
						} 
						else { //Create/re-use an existing menu. Will do for testing, but not a safe hash.
							CommandMenu storedMenu = (CommandMenu)menus.get( pathHistory + "." + token  );
							if( storedMenu != null ) {
								currentMenu = storedMenu;
							}
							else {
								CommandMenu newMenu = new CommandMenu(token);
								currentMenu.add(newMenu);
								currentMenu = newMenu;
								menus.put(pathHistory + "." + token  , newMenu );
							}
							pathHistory.append(token);
							pathHistory.append(".");
							depth++;
						}
					}
				} 
				else {
					rootMenu.add(new UndoableCommand(new InsertImageCommand(name, path, this, _pmwikisource.getPmWikiParameter(PmWikiSource.PARAMETER_RESOURCESURL))));
				}
			}
			return rootMenu;
		}
		else {
			return null;
		}
	}
		
	/**
   * convert Image to GIF-encoded data, reducing the number of colors if needed.
   * Added by Bertrand Delacretaz
   */
  public char[] convertToGif(Image oImgBuffer) throws IOException
  {
    System.err.println("converting data to GIF...");
    Graphics oGrf = oImgBuffer.getGraphics();
    
    
    getDesktop().getActiveDrawingView().clearSelection();
    
    PointConstrainer oldConstrainer = this.view().getConstrainer();

    PmWikiDrawingView view = (PmWikiDrawingView) this.view();
    // Remove the grid constrainer, should *guarantee* we don't get any extraneous grid lines!
    view.setConstrainer(null);
    
    // Force AA on the output image.
    boolean oldQualityMode = view.getQualityMode();
    view.setQualityMode(true);
    
    // Render the current drawing
    view.drawAll(oGrf);
    view.setConstrainer(oldConstrainer);
    view.setQualityMode(oldQualityMode);
    
    // test gif image:
/*    TestFrame tf = new TestFrame( "tt2: " + oImgBuffer.toString() );
    tf.setSize(new Dimension(oImgBuffer.getWidth(null)+30, oImgBuffer.getHeight(null)+30));
    tf.setImage(oImgBuffer);
    tf.show();
*/
    ByteArrayOutputStream oOut = null;

    try
    {
      oOut = new ByteArrayOutputStream();
      new GifEncoder(oImgBuffer, oOut).encode();
    } catch (IOException ioe)
    {
      // GifEncoder throws IOException when GIF contains too many colors
      // if this happens, filter image to reduce number of colors
      System.err.println("GIF uses too many colors, reducing to 216 colors...");
      final FilteredImageSource filter = new FilteredImageSource(oImgBuffer.getSource(),new Web216ColorsFilter());
      oOut = new ByteArrayOutputStream();
      new GifEncoder(filter,oOut).encode (); 
      System.err.println("Color reduction successful.");
    }

    byte[] aByte = oOut.toByteArray();
    int size = oOut.size();
    char[] aChar = new char[size];
    for (int i = 0; i < size; i++)
    {
      aChar[i] = (char) aByte[i];
    }
    System.err.println("conversion to GIF successful.");
    return aChar;
  }
  /* (non-Javadoc)
   * @see org.jhotdraw.application.DrawApplication#open()
   */
/*  public void open()
  {
    super.open();
    System.err.println("I'm here");
    loadDrawing(new StandardStorageFormat(), "MyFile");
  }*/
  

  //------------------------- Storage overrides ----------------------------------
	private void initDrawing() {
	  fDrawing = createDrawing();
		view().setDrawing(fDrawing);
		toolDone();
	}
  
	protected void loadDrawing(String param) {
		if (param == fgUntitled) {
		  getDesktop().getActiveDrawingView().drawing().release();
			initDrawing();
			return;
		}
		
		if(fDrawing == null) {
		  fDrawing = view().drawing();
		}

		String filename = _pmwikisource.getPmWikiParameter(param);
		if (filename != null) {
			readDrawing(filename);
		}
	}

	private void readDrawing(String filename) {
		toolDone();
		String type = guessType(filename);
		if (type.equals("storable")) {
			readFromStorableInput(filename);
		}
		else if (type.equals("serialized")) {
			readFromObjectInput(filename);
		}
		else {
			showStatus("Unknown file type");
		}
	}

	private void readFromStorableInput(String filename) {
		try {
			InputStream stream = null;
			if(filename.startsWith("http")) {
				URL url = _pmwikisource.createUrl(filename);
				stream = url.openStream();
			} 
			else {
				stream = new FileInputStream(filename);
			}

			// Use the converter to upgrade older drawing versions. [and do pre-processor tasks]
			PmWikiDrawingConverter converter = new PmWikiDrawingConverter();
			converter.convert(stream);
			
			StorableInput input = new StorableInput(converter.getConvertedStream());
			fDrawing.release();

			fDrawing = (Drawing)input.readStorable();
			if(fDrawing == null) {
				initDrawing();
				showStatus("There was a problem with the drawing in "+ filename);
			} else {
				view().setDrawing(fDrawing);
			}
		}
		catch (Exception e) {
			e.printStackTrace();
			initDrawing();
			showStatus("Error:" + e);
		}
	}

	private void readFromObjectInput(String filename) {
		try {
			URL url = _pmwikisource.createUrl(filename);
			InputStream stream = url.openStream();
			ObjectInput input = new ObjectInputStream(stream);
			fDrawing.release();
			fDrawing = (Drawing)input.readObject();
			view().setDrawing(fDrawing);
		}
		catch (IOException e) {
			initDrawing();
			showStatus("Error: " + e);
		}
		catch (ClassNotFoundException e) {
			initDrawing();
			showStatus("Class not found: " + e);
		}
	}

	private String guessType(String file) {
		if (file.endsWith(".draw")) {
			return "storable";
		}
		if (file.endsWith(".ser")) {
			return "serialized";
		}
		return "unknown";
	}  
  
	/**
	 * Sets the default tool of the editor.
	 * @see DrawingEditor
	 */
/*	public void toolDone() {
	  // Do nothing...
	}*/
	
	
	/**
	 * Creates the tool palette.
	 */
	protected JToolBar createToolPalette() {
		JToolBar palette = new CustomToolBar();
		palette.setBackground(Color.lightGray);
		return palette;
	}	
	
	/**
	 * Creates an action button with the given image, action, and text
	 */
	protected CommandButton createCommandButton(String iconName, String toolName, Command cmd) {
		return new CommandButton((PaletteListener)this, iconName, toolName, cmd);
	}
	/**
	 * Handles a user selection in the palette.
	 * @see PaletteListener
	 */
	public void paletteUserSelected(PaletteButton paletteButton) {
		if(paletteButton instanceof ToolButton) {
			super.paletteUserSelected(paletteButton);
		} 
		else {
			CommandButton cmdButton = (CommandButton)paletteButton;
		}
	}

	/**
	 * Handles when the mouse enters or leaves a palette button.
	 * @see PaletteListener
	 */
	public void paletteUserOver(PaletteButton paletteButton, boolean inside) {
		if(paletteButton instanceof ToolButton) {
			super.paletteUserOver(paletteButton, inside);
		} else {
			CommandButton cmdButton = (CommandButton)paletteButton;
			if (inside) {
				showStatus(cmdButton.name());
			} else {
				//reset status
			}
			
		}
	}
	
	/* (non-Javadoc)
	 * @see org.jhotdraw.application.DrawApplication#addListeners()
	 */
	protected void addListeners() {
		addWindowListener(new WindowAdapter() {
			/* (non-Javadoc)
			 * @see java.awt.event.WindowAdapter#windowClosing(java.awt.event.WindowEvent)
			 */
			public void windowClosing(WindowEvent arg0) {
				endApp(false);
			}
		});
	}
  
  /**
   * Creates the selection tool used in this editor. Override to use
   * a custom selection tool.
   */
  protected Tool createSelectionTool() {
    return new PmWikiDrawSelectionTool(this);
  }  
}