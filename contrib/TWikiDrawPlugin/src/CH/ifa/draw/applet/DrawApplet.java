/*
 * @(#)DrawApplet.java 5.1
 *
 */

package CH.ifa.draw.applet;

import java.applet.Applet;
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
 * DrawApplication defines a standard presentation for
 * a drawing editor that is run as an applet. The presentation is
 * customized in subclasses.<p>
 * Supported applet parameters: <br>
 * <i>DRAWINGS</i>: a blank separated list of drawing names that is
 *           shown in the drawings choice.
 */

public class DrawApplet
        extends Applet
	    implements DrawingEditor, PaletteListener {

    transient private Drawing         fDrawing;
    transient private Tool            fTool;

    transient private StandardDrawingView fView;
    transient private ToolButton      fDefaultToolButton;
    transient private ToolButton      fSelectedToolButton;

    transient private boolean         fSimpleUpdate;
    transient private Button          fUpdateButton;

    transient private Choice          fFrameColor;
    transient private Choice          fFillColor;
    //transient private Choice          fTextColor;
    transient private Choice          fArrowChoice;
    transient private Choice          fFontChoice;

    transient private Thread          fSleeper;
    private Iconkit                   fIconkit;

    static String                     fgUntitled = "untitled";

    private static final String       fgDrawPath = "/CH/ifa/draw/";
    public static final String        IMAGES = fgDrawPath+"images/";

    /**
     * Initializes the applet and creates its contents.
     */
    public void init() {
        fIconkit = new Iconkit(this);

		setLayout(new BorderLayout());

        fView = createDrawingView();

        Panel attributes = createAttributesPanel();
        createAttributeChoices(attributes);
        add("North", attributes);

        Panel toolPanel = createToolPalette();
        createTools(toolPanel);
        add("West", toolPanel);

        add("Center", fView);
        Panel buttonPalette = createButtonPanel();
        createButtons(buttonPalette);
        add("South", buttonPalette);

        initDrawing();
        setBufferedDisplayUpdate();
        setupAttributes();
    }

    /*
     * Gets the iconkit to be used in the applet.
     */

     /**** not sure whether this will still be needed on 1.1 enabled browsers
     protected Iconkit iconkit() {
        if (fIconkit == null) {

            startSleeper();
            loadAllImages(this); // blocks until images loaded
            stopSleeper();
        }
        return fIconkit;
    } */

    /**
     * Creates the attributes panel.
     */
    protected Panel createAttributesPanel() {
        Panel panel = new Panel();
        panel.setLayout(new PaletteLayout(2, new Point(2,2), false));
        return panel;
    }

    /**
     * Creates the attribute choices. Override to add additional
     * choices.
     */
    protected void createAttributeChoices(Panel panel) {
        panel.add(new Label("Fill"));
        fFillColor = createColorChoice("FillColor");
        panel.add(fFillColor);

        //panel.add(new Label("Text"));
        //fTextColor = createColorChoice("TextColor");
        //panel.add(fTextColor);

        panel.add(new Label("Pen"));
        fFrameColor = createColorChoice("FrameColor");
        panel.add(fFrameColor);

        panel.add(new Label("Arrow"));
        CommandChoice choice = new CommandChoice();
        fArrowChoice = choice;
        choice.addItem(new ChangeAttributeCommand("none",     "ArrowMode", new Integer(PolyLineFigure.ARROW_TIP_NONE),  fView));
        choice.addItem(new ChangeAttributeCommand("at Start", "ArrowMode", new Integer(PolyLineFigure.ARROW_TIP_START), fView));
        choice.addItem(new ChangeAttributeCommand("at End",   "ArrowMode", new Integer(PolyLineFigure.ARROW_TIP_END),   fView));
        choice.addItem(new ChangeAttributeCommand("at Both",  "ArrowMode", new Integer(PolyLineFigure.ARROW_TIP_BOTH),  fView));
        panel.add(fArrowChoice);

        panel.add(new Label("Font"));
        fFontChoice = createFontChoice();
        panel.add(fFontChoice);
    }

    /**
     * Creates the color choice for the given attribute.
     */
    protected Choice createColorChoice(String attribute) {
        CommandChoice choice = new CommandChoice();
	ColorMap map = ColorMap.getColorMap();
        for (int i=0; i < map.size(); i++)
            choice.addItem(
                new ChangeAttributeCommand(
                    map.name(i), attribute,
                    map.color(i),
                    fView
                )
            );
        return choice;
    }

    /**
     * Creates the font choice. The choice is filled with
     * all the fonts supported by the toolkit.
     */
    protected Choice createFontChoice() {
        CommandChoice choice = new CommandChoice();
        String fonts[] = Toolkit.getDefaultToolkit().getFontList();
        for (int i = 0; i < fonts.length; i++)
            choice.addItem(new ChangeAttributeCommand(fonts[i], "FontName", fonts[i],  fView));
        return choice;
    }

    /**
     * Creates the buttons panel.
     */
    protected Panel createButtonPanel() {
        Panel panel = new Panel();
        panel.setLayout(new PaletteLayout(2, new Point(2,2), false));
        return panel;
    }

    /**
     * Creates the buttons shown in the buttons panel. Override to
     * add additional buttons.
     * @param panel the buttons panel.
     */
    protected void createButtons(Panel panel) {
        panel.add(new Filler(24,20));

        Choice drawingChoice = new Choice();
        drawingChoice.addItem(fgUntitled);

	    String param = getParameter("DRAWINGS");
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

        // panel.add(fUpdateButton); // not shown currently
    }

    /**
     * Creates the tools palette.
     */
    protected Panel createToolPalette() {
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
    protected void createTools(Panel palette) {
        Tool tool = createSelectionTool();

        fDefaultToolButton = createToolButton(IMAGES+"SEL", "Selection Tool", tool);
        palette.add(fDefaultToolButton);
    }

    /**
     * Creates the selection tool used in this editor. Override to use
     * a custom selection tool.
     */
    protected Tool createSelectionTool() {
        return new SelectionTool(view());
    }

    /**
     * Creates a tool button with the given image, tool, and text
     */
    protected ToolButton createToolButton(String iconName, String toolName, Tool tool) {
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
        setupAttributes();
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

        String filename = getParameter(param);
        if (filename != null)
            readDrawing(filename);
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
            URL url = new URL(getCodeBase(), filename);
            InputStream stream = url.openStream();
            StorableInput input = new StorableInput(stream);
            fDrawing.release();

            fDrawing = (Drawing)input.readStorable();
            fView.setDrawing(fDrawing);
        } catch (IOException e) {
            initDrawing();
            showStatus("Error:"+e);
        }
    }

    private void readFromObjectInput(String filename) {
        try {
            URL url = new URL(getCodeBase(), filename);
            InputStream stream = url.openStream();
            ObjectInput input = new ObjectInputStream(stream);
            fDrawing.release();
            fDrawing = (Drawing)input.readObject();
            fView.setDrawing(fDrawing);
        } catch (IOException e) {
            initDrawing();
            showStatus("Error: " + e);
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

    private void setupAttributes() {
        Color frameColor =
	    (Color)AttributeFigure.getDefaultAttribute("FrameColor");
        Color fillColor =
	    (Color)AttributeFigure.getDefaultAttribute("FillColor");
        Color textColor =
	    (Color)AttributeFigure.getDefaultAttribute("TextColor");
        Integer arrowMode =
	    (Integer)AttributeFigure.getDefaultAttribute("ArrowMode");
        String fontName =
	    (String)AttributeFigure.getDefaultAttribute("FontName");

        FigureEnumeration k = fView.selectionElements();
        while (k.hasMoreElements()) {
            Figure f = k.nextFigure();
            frameColor = (Color) f.getAttribute("FrameColor");
            fillColor  = (Color) f.getAttribute("FillColor");
            textColor  = (Color) f.getAttribute("TextColor");
            arrowMode  = (Integer) f.getAttribute("ArrowMode");
            fontName   = (String) f.getAttribute("FontName");
        }

        fFrameColor.select(ColorMap.getColorMap().colorIndex(frameColor));
        fFillColor.select(ColorMap.getColorMap().colorIndex(fillColor));
        //fTextColor.select(ColorMap.colorIndex(textColor));
        if (arrowMode != null)
            fArrowChoice.select(arrowMode.intValue());
        if (fontName != null)
            fFontChoice.select(fontName);
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
     * Shows a help page for the applet. The URL of the help
     * page is derived as follows: codeBase+appletClassname+Help.html"
     */
    protected void showHelp() {
        try {
            String appletPath = getClass().getName().replace('.', '/');
            URL url = new URL(getCodeBase(), appletPath+"Help.html");
            getAppletContext().showDocument(url, "Help");
        } catch (IOException e) {
            showStatus("Help file not found");
        }

    }

    /**
     * *** netscape browser work around ***
     */
    private void startSleeper() {
        if (fSleeper == null)
            fSleeper = new SleeperThread(this);
        fSleeper.start();
    }

    private void stopSleeper() {
        if (fSleeper != null)
            fSleeper.stop();
    }
}


class SleeperThread extends Thread {

    Applet  fApplet;

    SleeperThread(Applet applet) {
        fApplet = applet;
    }

    public void run() {
        try {
            for (;;) {
                fApplet.showStatus("loading icons...");
                sleep(50);
            }
        } catch (InterruptedException e) {
            return;
        }
    }

}

