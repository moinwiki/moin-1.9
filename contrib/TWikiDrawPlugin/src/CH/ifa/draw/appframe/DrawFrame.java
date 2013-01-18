/*
 * Copyright (C) 2001 Motorola - All rights reserved
 *
 * Portions Copyright 2000 by Peter Thoeny, Peter@Thoeny.com.
 * It is hereby granted that this software can be used, copied, 
 * modified, and distributed without fee provided that this 
 * copyright notice appears in all copies.
 * Portions Copyright (C) 2001 Motorola - All rights reserved
 */

package CH.ifa.draw.appframe;

import java.awt.*;
import java.awt.event.*;
import java.util.*;
import java.io.*;
import java.net.*;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.*;
import CH.ifa.draw.figures.*;
import CH.ifa.draw.util.*;

/**
 * Base class of drawing editor frames.
 * Provides support for drawing editors such that they are created in
 * a Frame, so that all the facilities of AWT (such as Menus) are
 * available. Provides basically the same facilities as a DrawApplet
 * and is designed to be overridden to add extra menus and buttons.
 */
public class DrawFrame extends Frame
    implements DrawingEditor, PaletteListener {

    transient private Drawing         fDrawing;
    transient private Tool            fTool;

    transient private StandardDrawingView fView;
    transient private ToolButton      fDefaultToolButton;
    transient private ToolButton      fSelectedToolButton;

    transient private boolean         fSimpleUpdate;
    transient private Button          fUpdateButton;

    transient private Panel	      fPanel;

    private Iconkit                   fIconkit;

    static String                     fgUntitled = "untitled";

    private static final String       fgDrawPath = "/CH/ifa/draw/";
    public static final String        IMAGES = fgDrawPath+"images/";

    private Application       fApplication;

    public DrawFrame(String title, Application application) {
	super(title);

	fApplication = application;

        fIconkit = new Iconkit(this);

	setLayout(new BorderLayout());

        fView = createDrawingView();

	MenuBar mb = new MenuBar();
        populateMenuBar(mb);
	setMenuBar(mb);

	Panel panel = createSouthPanel();
	if (panel != null) {
	    populateSouthPanel(panel);
	    add("South", panel);
	}

	panel = createWestPanel();
	if (panel != null) {
	    populateWestPanel(panel);
	    add("West", panel);
	}

	panel = createEastPanel();
	if (panel != null) {
	    populateEastPanel(panel);
	    add("East", panel);
	}

	panel = createNorthPanel();
	if (panel != null) {
	    populateNorthPanel(panel);
	    add("North", panel);
	}

	ScrollPane sp = new ScrollPane();
	sp.add(fView);
	add("Center", sp);

        initDrawing();
        setBufferedDisplayUpdate();
        //setupAttributes();
    }

    public Application getApplication() {
	return fApplication;
    }

    public void showStatus(String s) {
	fApplication.showStatus(s);
    }

    protected void populateMenuBar(MenuBar mb) {
    }

    /**
     * Creates the buttons panel.
     */
    protected Panel createSouthPanel() {
        Panel panel = new Panel();
        panel.setLayout(new PaletteLayout(2, new Point(2,2), false));
        return panel;
    }

    /**
     * Creates the buttons shown in the buttons panel. Override to
     * add additional/alternative buttons.
     * @param panel the buttons panel.
     */
    protected void populateSouthPanel(Panel panel) {
        panel.add(new Filler(24,20));

        Choice drawingChoice = new Choice();
        drawingChoice.addItem(fgUntitled);

	String param = fApplication.getParameter("DRAWINGS");
	if (param == null)
	    param = "";
       	StringTokenizer st = new StringTokenizer(param);
        while (st.hasMoreTokens())
            drawingChoice.addItem(st.nextToken());
        // offer choice only if more than one
        if (drawingChoice.getItemCount() > 1)
            panel.add(drawingChoice);
        else
            panel.add(new Label(fgUntitled));

	drawingChoice.addItemListener(
	    new ItemListener() {
		    public void itemStateChanged(ItemEvent e) {
			if (e.getStateChange() == ItemEvent.SELECTED) {
			    loadDrawing((String)e.getItem());
			}
		    }
		}
	    );

        panel.add(new Filler(6,20));

        Button button;
        button = new CommandButton(new DeleteCommand("Delete", fView));
        panel.add(button);

        button = new CommandButton(new DuplicateCommand("Duplicate", fView));
        panel.add(button);

        button = new CommandButton(new GroupCommand("Group", fView));
        panel.add(button);

        button = new CommandButton(new UngroupCommand("Ungroup", fView));
        panel.add(button);

        button = new Button("Help");
	button.addActionListener(
	    new ActionListener() {
		    public void actionPerformed(ActionEvent event) {
			showHelp();
		    }
		}
	    );
        panel.add(button);

	fUpdateButton = new Button("Simple Update");
	fUpdateButton.addActionListener(
	    new ActionListener() {
		    public void actionPerformed(ActionEvent event) {
			if (fSimpleUpdate)
			    setBufferedDisplayUpdate();
			else
			    setSimpleDisplayUpdate();
		    }
		}
	    );
	
	panel.add(fUpdateButton);
    }

    /**
     * Creates the color choice for the given attribute.
     */
    protected CommandMenu createColorMenu(String attribute) {
        CommandMenu menu = new CommandMenu("Colour");
	ColorMap map = ColorMap.getColorMap();
        for (int i = 0; i < map.size(); i++)
            menu.add(
                new ChangeAttributeCommand(
                    map.name(i), attribute,
                    map.color(i), fView));
        return menu;
    }

    /**
     * Creates the font choice. The choice is filled with
     * all the fonts supported by the toolkit.
     */
    protected CommandMenu createFontMenu() {
        CommandMenu menu = new CommandMenu("Font");

	/** If we were able to assume 1.2 or greater, we would get
	 * the fonts list like this:
        String[] font =
	    GraphicsEnvironment.getLocalGraphicsEnvironment().
	    getAvailableFontFamilyNames();
	*/
	
        String fonts[] = Toolkit.getDefaultToolkit().getFontList();

        for (int i = 0; i < fonts.length; i++)
            menu.add(
		new ChangeAttributeCommand(
		    fonts[i], "FontName", fonts[i],  fView));
        return menu;
    }

    protected Panel createEastPanel() {
	return null;
    }

    protected void populateEastPanel(Panel panel) {
    }

    protected Panel createNorthPanel() {
	return null;
    }

    protected void populateNorthPanel(Panel panel) {
    }

    /**
     * Creates the tools palette.
     */
    protected Panel createWestPanel() {
        Panel palette = new Panel();
        palette.setLayout(new PaletteLayout(2,new Point(2,2)));
        return palette;
    }

    /**
     * Creates the tools. By default only the selection tool is added.
     * Override this method to add additional tools.
     * Call the inherited method to include the selection tool.
     * @param palette the palette where the tools are added.
     */
    protected void populateWestPanel(Panel palette) {
        Tool tool = createSelectionTool();

        fDefaultToolButton = createToolButton(
	    IMAGES+"SEL", "Selection Tool", tool);
        palette.add(fDefaultToolButton);
    }

    /**
     * Creates the selection tool used in this editor. Override to use
     * a custom selection tool.
     */
    protected Tool createSelectionTool() {
        return new SelectionTool(fView);
    }

    /**
     * Creates a tool button with the given image, tool, and text
     */
    protected ToolButton createToolButton(String iconName,
					  String toolName, Tool tool) {
        return new ToolButton(this, iconName, toolName, tool);
    }

    /**
     * Creates the drawing used in this application.
     * You need to override this method to use a Drawing
     * subclass in your application. By default a standard
     * Drawing is returned.
     */
    protected Drawing createDrawing() {
        return new StandardDrawing();
    }

    /**
     * Creates the drawing view used in this application.
     * You need to override this method to use a DrawingView
     * subclass in your application. By default a standard
     * DrawingView is returned.
     */
    protected StandardDrawingView createDrawingView() {
        return new StandardDrawingView(this, 410, 370);
    }

    /**
     * Handles a user selection in the palette.
     * @see PaletteListener
     */
    public void paletteUserSelected(PaletteButton button) {
        ToolButton toolButton = (ToolButton) button;
        setTool(toolButton.tool(), toolButton.name());
        setSelected(toolButton);
    }

    /**
     * Handles when the mouse enters or leaves a palette button.
     * @see PaletteListener
     */
    public void paletteUserOver(PaletteButton button, boolean inside) {
        if (inside)
            showStatus(((ToolButton) button).name());
        else
            showStatus(fSelectedToolButton.name());
    }

    /**
     * Gets the current drawing.
     * @see DrawingEditor
     */
    public Drawing drawing() {
        return fDrawing;
    }

    /**
     * Gets the current tool.
     * @see DrawingEditor
     */
    public Tool tool() {
        return fTool;
    }

    /**
     * Gets the current drawing view.
     * @see DrawingEditor
     */
    public DrawingView view() {
        return fView;
    }

    /**
     * Sets the default tool of the editor.
     * @see DrawingEditor
     */
    public void toolDone() {
        setTool(fDefaultToolButton.tool(), fDefaultToolButton.name());
        setSelected(fDefaultToolButton);
    }

    /**
     * Handles a change of the current selection. Updates all
     * menu items that are selection sensitive.
     * @see DrawingEditor
     */
    public void selectionChanged(DrawingView view) {
        //setupAttributes();
    }

    private void initDrawing() {
        fDrawing = createDrawing();
        fView.setDrawing(fDrawing);
        toolDone();
    }

    private void setTool(Tool t, String name) {
        if (fTool != null)
            fTool.deactivate();
        fTool = t;
        if (fTool != null) {
            showStatus(name);
            fTool.activate();
        }
    }

    private void setSelected(ToolButton button) {
        if (fSelectedToolButton != null)
            fSelectedToolButton.reset();
        fSelectedToolButton = button;
        if (fSelectedToolButton != null)
            fSelectedToolButton.select();
    }

    protected void loadDrawing(String param) {
        if (param == fgUntitled) {
            fDrawing.release();
            initDrawing();
            return;
        }

        String filename = fApplication.getParameter(param);
        if (filename != null) {
	    readDrawing(filename);
	}
    }

    private void readDrawing(String filename) {
        toolDone();
        String type = guessType(filename);
        if (type.equals("storable"))
            readFromStorableInput(filename);
        else if (type.equals("serialized"))
            readFromObjectInput(filename);
        else
            showStatus("Unknown file type");
    }

    private void readFromStorableInput(String filename) {
        try {
            URL url = fApplication.getURL(filename);
            InputStream stream = url.openStream();
            StorableInput input = new StorableInput(stream);
            fDrawing.release();

            fDrawing = (Drawing)input.readStorable();
            fView.setDrawing(fDrawing);
        } catch (IOException e) {
            initDrawing();
            showStatus("Error reading " + filename + ": "+e);
	    e.printStackTrace();
        }
    }

    private void readFromObjectInput(String filename) {
        try {
            URL url = fApplication.getURL(filename);
            InputStream stream = url.openStream();
            ObjectInput input = new ObjectInputStream(stream);
            fDrawing.release();
            fDrawing = (Drawing)input.readObject();
            fView.setDrawing(fDrawing);
        } catch (IOException e) {
            initDrawing();
            showStatus("Error reading (OI) " + filename + ": " + e);
	    e.printStackTrace();
        } catch (ClassNotFoundException e) {
            initDrawing();
            showStatus("Class not found: " + e);
        }
    }

    private String guessType(String file) {
        if (file.endsWith(".draw"))
            return "storable";
        if (file.endsWith(".ser"))
            return "serialized";
        return "unknown";
    }

    protected void setSimpleDisplayUpdate() {
        fView.setDisplayUpdate(new SimpleUpdateStrategy());
        fUpdateButton.setLabel("Simple Update");
        fSimpleUpdate = true;
    }

    protected void setBufferedDisplayUpdate() {
        fView.setDisplayUpdate(new BufferedUpdateStrategy());
        fUpdateButton.setLabel("Buffered Update");
        fSimpleUpdate = false;
    }

    /**
     * Shows a help page for the application. The URL of the help
     * page is derived as follows: codeBase+applicationClassname+Help.html"
     */
    protected void showHelp() {
        try {
            String helpPath = getClass().getName().replace('.', '/');
            URL url = fApplication.getURL(helpPath + "Help.html");
            fApplication.popupFrame(url, "Help");
        } catch (IOException e) {
            showStatus("Help file not found");
        }
    }
}

