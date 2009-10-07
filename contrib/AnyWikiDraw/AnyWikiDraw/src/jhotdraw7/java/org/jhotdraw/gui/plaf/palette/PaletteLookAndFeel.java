/**
 * @(#)PaletteLookAndFeel.java
 *
 * Copyright (c) 2008 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.gui.plaf.palette;

import java.awt.*;
import javax.swing.*;
import javax.swing.UIDefaults.*;
import javax.swing.border.Border;
import javax.swing.plaf.*;
import javax.swing.plaf.basic.*;

/**
 * A LookAndFeel for components in the palette windows of a drawing editor.
 *
 * @author Werner Randelshofer
 * @version $Id: PaletteLookAndFeel.java 538 2009-06-17 14:46:51Z rawcoder $
 */
public class PaletteLookAndFeel extends BasicLookAndFeel {

    /** 
     * Shared instance.
     */
    private static PaletteLookAndFeel instance;
    /**
     * Cached defaults.
     */
    private UIDefaults cachedDefaults;

    public static PaletteLookAndFeel getInstance() {
        if (instance == null) {
            instance = new PaletteLookAndFeel();
        }
        return instance;
    }

    @Override
    public String getName() {
        return "Palette Look and Feel";
    }

    @Override
    public String getID() {
        return "Palette";
    }

    @Override
    public String getDescription() {
        return "A look and feel for palette components";
    }

    @Override
    public boolean isNativeLookAndFeel() {
        return false;
    }

    @Override
    public boolean isSupportedLookAndFeel() {
        return true;
    }

    public UIDefaults getCachedDefaults() {
        if (cachedDefaults == null) {
            cachedDefaults = getDefaults();
        }
        return cachedDefaults;
    }

    /**
     * Looks up up the given key in our Hashtable and resolves LazyValues
     * or ActiveValues.
     */
    public Object get(Object key) {
        UIDefaults defaults = getCachedDefaults();

        /* Quickly handle the common case, without grabbing
         * a lock.
         */
        Object value = defaults.get(key);
        if (!(value instanceof ActiveValue) &&
                !(value instanceof LazyValue)) {
            return value;
        }

        /* At this point we know that the value of key was
         * a LazyValue or an ActiveValue.
         */
        if (value instanceof LazyValue) {
            try {
                /* If an exception is thrown we'll just put the LazyValue
                 * back in the table.
                 */
                value = ((LazyValue) value).createValue(defaults);
            } finally {
                if (value == null) {
                    defaults.remove(key);
                } else {
                    defaults.put(key, value);
                }
            }
        } else {
            value = ((ActiveValue) value).createValue(defaults);
        }
        return value;
    }

    public Font getFont(String key) {
        return (Font) get(key);
    }

    public Border getBorder(String key) {
        return (Border) get(key);
    }

    public Color getColor(String key) {
        return (Color) get(key);
    }

    public Insets getInsets(String key) {
        return (Insets) get(key);
    }
    public boolean getBoolean(String key) {
        return ((Boolean) get(key)).booleanValue();
    }

    /**
     * Convenience method for initializing a components foreground
     * background and font properties with values from the current
     * defaults table.  The properties are only set if the current
     * value is either null or a UIResource.
     * 
     * @param c the target component for installing default color/font properties
     * @param defaultBgName the key for the default background
     * @param defaultFgName the key for the default foreground
     * @param defaultFontName the key for the default font
     * 
     * @see #installColors
     * @see UIManager#getColor
     * @see UIManager#getFont
     */
    public static void installColorsAndFont(JComponent c,
            String defaultBgName,
            String defaultFgName,
            String defaultFontName) {
        Font f = c.getFont();
        if (f == null || f instanceof UIResource) {
            c.setFont(getInstance().getFont(defaultFontName));
        }

        installColors(c, defaultBgName, defaultFgName);
    }

    /**
     * Convenience method for installing a component's default Border 
     * object on the specified component if either the border is 
     * currently null or already an instance of UIResource.
     * @param c the target component for installing default border
     * @param defaultBorderName the key specifying the default border
     */
    public static void installBorder(JComponent c, String defaultBorderName) {
        Border b = c.getBorder();
        //if (b == null || b instanceof UIResource) {
        c.setBorder(getInstance().getBorder(defaultBorderName));
    //}

    }

    /**
     * Convenience method for initializing a component's foreground
     * and background color properties with values from the current
     * defaults table.  The properties are only set if the current
     * value is either null or a UIResource.
     * 
     * @param c the target component for installing default color/font properties
     * @param defaultBgName the key for the default background
     * @param defaultFgName the key for the default foreground
     * 
     * @see #installColorsAndFont
     * @see UIManager#getColor
     */
    public static void installColors(JComponent c,
            String defaultBgName,
            String defaultFgName) {
        Color bg = c.getBackground();
        if (bg == null || bg instanceof UIResource) {
            c.setBackground(getInstance().getColor(defaultBgName));
        }

        Color fg = c.getForeground();
        if (fg == null || fg instanceof UIResource) {
            c.setForeground(getInstance().getColor(defaultFgName));
        }
    }

    @Override
    protected void initComponentDefaults(UIDefaults table) {
        super.initComponentDefaults(table);

        table.addResourceBundle("org.jhotdraw.gui.Labels");

        // *** Shared Fonts
        Integer eleven = new Integer(11);
        Integer twelve = new Integer(12);
        Integer fontPlain = new Integer(Font.PLAIN);
        Integer fontBold = new Integer(Font.BOLD);
        Object dialogPlain11 = new ProxyLazyValue(
                "javax.swing.plaf.FontUIResource",
                null,
                new Object[]{"Dialog Sans", fontPlain, eleven});
        Object dialogPlain12 = new ProxyLazyValue(
                "javax.swing.plaf.FontUIResource",
                null,
                new Object[]{"Dialog Sans", fontPlain, twelve});
        Object fieldPlain12 = new ProxyLazyValue(
                "javax.swing.plaf.FontUIResource",
                null,
                new Object[]{"Verdana", fontPlain, twelve});
        Object serifPlain12 = new ProxyLazyValue(
                "javax.swing.plaf.FontUIResource",
                null,
                new Object[]{"Serif", fontPlain, twelve});
        Object sansSerifPlain12 = new ProxyLazyValue(
                "javax.swing.plaf.FontUIResource",
                null,
                new Object[]{"SansSerif", fontPlain, twelve});
        Object monospacedPlain12 = new ProxyLazyValue(
                "javax.swing.plaf.FontUIResource",
                null,
                new Object[]{"MonoSpaced", fontPlain, twelve});
        Object dialogBold12 = new ProxyLazyValue(
                "javax.swing.plaf.FontUIResource",
                null,
                new Object[]{"Dialog", fontBold, twelve});


        // *** Shared Colors
        ColorUIResource black = new ColorUIResource(Color.black);

        ColorUIResource control = new ColorUIResource(0xf0f0f0);
        ColorUIResource controlText = black;

        ColorUIResource selectionBackground = new ColorUIResource(0xb5d5ff);
        ColorUIResource selectionForeground = black;

        // *** Shared Insets
        InsetsUIResource zeroInsets = new InsetsUIResource(0, 0, 0, 0);
        InsetsUIResource twoInsets = new InsetsUIResource(2, 2, 2, 2);

        // *** Shared Borders
	/*Object buttonBorder = 
        new ProxyLazyValue(
        "org.jhotdraw.gui.plaf.palette.BackdropBorder$UIResource",
        new Object[] {new PaletteButtonBorder()});*/
        Object buttonBorder = new BackdropBorder.UIResource(new PaletteButtonBorder());
        Object textBorder = new BackdropBorder.UIResource(new PaletteTextComponentBorder());

        Object[] defaults = {
            // *** Fonts
            "SmallSystemFont", dialogPlain11,

            // *** Buttons
            "Button.font", dialogPlain12,
            "Button.background", control,
            "Button.foreground", controlText,
            "Button.border", buttonBorder,
            "Button.margin", zeroInsets,
            // *** FontChooser
            "Button.background", control,
            "Button.foreground", controlText,
            "Button.border", buttonBorder,
            "Button.margin", zeroInsets,
            // *** FormattedTextField
            "FormattedTextField.font", fieldPlain12,
            "FormattedTextField.background", control,
            "FormattedTextField.foreground", controlText,
            "FormattedTextField.border", textBorder,
            "FormattedTextField.margin", zeroInsets,
            "FormattedTextField.opaque", Boolean.TRUE,
            "FormattedTextField.errorIndicatorForeground", new ColorUIResource(0xfe4a41),
            "FormattedTextField.selectionBackground", selectionBackground,
            "FormattedTextField.selectionForeground",  selectionForeground,
            // *** Labels
            "Label.font", dialogPlain12,
            // *** Ribbons
            "Ribbon.border", new UIDefaults.ProxyLazyValue("javax.swing.border.MatteBorder", new Object[] {new Insets(1,0,0,0), new Color(0x777777)}), //
            // *** ScrollPane
            "ScrollPane.border", new UIDefaults.ProxyLazyValue("javax.swing.border.MatteBorder", new Object[] {new Insets(1,1,1,1), new Color(0xa5a5a5)}), //
            // *** Slider
            "Slider.background", control,
            "Slider.foreground", controlText,
            "Slider.horizontalSize", new DimensionUIResource(100, 20),
            "Slider.verticalSize", new DimensionUIResource(20, 100),
            // *** TextArea
            "TextArea.selectionBackground", selectionBackground,
            "TextArea.selectionForeground",  selectionForeground,
            // *** TextField
            "TextField.font", fieldPlain12,
            "TextField.background", control,
            "TextField.foreground", controlText,
            "TextField.border", textBorder,
            "TextField.margin", zeroInsets,
            "TextField.opaque", Boolean.TRUE,
            "TextField.selectionBackground", selectionBackground,
            "TextField.selectionForeground",  selectionForeground,
            // *** ToolBar
            "ToolBar.font", dialogPlain12,
            "ToolBar.background", control,
            "ToolBar.foreground", controlText,
            "ToolBar.dockingBackground", control,
            //	    "ToolBar.dockingForeground", red,
            "ToolBar.floatingBackground", control,
            //	    "ToolBar.floatingForeground", darkGray,
            //	    "ToolBar.border", etchedBorder,
            "ToolBar.border", new UIDefaults.ProxyLazyValue("org.jhotdraw.gui.plaf.palette.PaletteToolBarBorder$UIResource"), //
            //	    "ToolBar.separatorSize", toolBarSeparatorSize,
        };

        table.putDefaults(defaults);
    }

    /**
     * Returns the ui that is of type <code>klass</code>, or null if
     * one can not be found.
     */
    static Object getUIOfType(ComponentUI ui, Class klass) {
        if (klass.isInstance(ui)) {
            return ui;
        }
        return null;
    }
}
