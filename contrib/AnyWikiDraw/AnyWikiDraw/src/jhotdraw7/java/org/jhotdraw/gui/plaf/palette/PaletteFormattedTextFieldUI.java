/**
 * @(#)PaletteTextFieldUI.java
 *
 * Copyright (c) 2009 by the original authors of JHotDraw
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
import java.awt.geom.Line2D;
import javax.swing.*;
import javax.swing.border.Border;
import javax.swing.plaf.*;
import javax.swing.plaf.basic.*;
import javax.swing.text.*;

/**
 * PaletteFormattedTextFieldUI.
 *
 * @author Werner Randelshofer
 * @version $Id: PaletteFormattedTextFieldUI.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class PaletteFormattedTextFieldUI extends BasicFormattedTextFieldUI {
    private Color errorIndicatorForeground;

    /**
     * Creates a UI for a JTextField.
     *
     * @param c the text field
     * @return the UI
     */
    public static ComponentUI createUI(JComponent c) {
        return new PaletteFormattedTextFieldUI();
    }

    /**
     * Creates a view (FieldView) based on an element.
     *
     * @param elem the element
     * @return the view
     */
    @Override
    public View create(Element elem) {
        /* We create our own view here. This view always uses the
         * text alignment that was specified by the text component. Even
         * then, when the text is longer than in the text component.
         *
         * Draws a wavy line if the value of the field is not valid.
         */
        return new FieldView(elem) {

            /**
             * Adjusts the allocation given to the view
             * to be a suitable allocation for a text field.
             * If the view has been allocated more than the
             * preferred span vertically, the allocation is
             * changed to be centered vertically.  Horizontally
             * the view is adjusted according to the horizontal
             * alignment property set on the associated JTextField
             * (if that is the type of the hosting component).
             *
             * @param a the allocation given to the view, which may need
             *  to be adjusted.
             * @return the allocation that the superclass should use.
             */
            protected Shape adjustAllocationXX(Shape a) {
                if (a != null) {
                    Rectangle bounds = a.getBounds();
                    int vspan = (int) getPreferredSpan(Y_AXIS);
                    int hspan = (int) getPreferredSpan(X_AXIS);
                    if (bounds.height != vspan) {
                        int slop = bounds.height - vspan;
                        bounds.y += slop / 2;
                        bounds.height -= slop;
                    }

                    // horizontal adjustments
                    Component c = getContainer();
                    if (c instanceof JTextField) {
                        JTextField field = (JTextField) c;
                        BoundedRangeModel vis = field.getHorizontalVisibility();
                        int max = Math.max(hspan, bounds.width);
                        int value = vis.getValue();
                        int extent = Math.min(max, bounds.width - 1);
                        if ((value + extent) > max) {
                            value = max - extent;
                        }
                        vis.setRangeProperties(value, extent, vis.getMinimum(),
                                max, false);
                        if (hspan < bounds.width) {
                            // horizontally align the interior
                            int slop = bounds.width - 1 - hspan;

                            int align = ((JTextField) c).getHorizontalAlignment();
                            if (true /*((JComponent) c).isLeftToRight()*/) {
                                if (align == LEADING) {
                                    align = LEFT;
                                } else if (align == TRAILING) {
                                    align = RIGHT;
                                }
                            } else {
                                if (align == LEADING) {
                                    align = RIGHT;
                                } else if (align == TRAILING) {
                                    align = LEFT;
                                }
                            }

                            switch (align) {
                                case SwingConstants.CENTER:
                                    bounds.x += slop / 2;
                                    bounds.width -= slop;
                                    break;
                                case SwingConstants.RIGHT:
                                    bounds.x += slop;
                                    bounds.width -= slop;
                                    break;
                            }
                        } else {
                            // adjust the allocation to match the bounded range.
                            bounds.width = hspan;
                            bounds.x -= vis.getValue();
                        }
                    }
                    return bounds;
                }
                return null;
            }

            @Override
            public void paint(Graphics gr, Shape a) {
                Graphics2D g = (Graphics2D) gr;
                JFormattedTextField editor = (JFormattedTextField) getComponent();
                if (!editor.isEditValid()) {
                    Rectangle r = (Rectangle) a;
                    g.setColor(errorIndicatorForeground);
                    g.setStroke(new BasicStroke(2.5f, BasicStroke.CAP_BUTT, BasicStroke.JOIN_BEVEL, 0, new float[]{3f,3f},0.5f));
                    g.draw(new Line2D.Float(r.x, r.y+r.height-0.5f, r.x+r.width-1,r.y+r.height-0.5f));
                    }
                    super.paint(g, a);
            }
        };
    }

    /**
     * Initializes component properties, e.g. font, foreground, 
     * background, caret color, selection color, selected text color,
     * disabled text color, and border color.  The font, foreground, and
     * background properties are only set if their current value is either null
     * or a UIResource, other properties are set if the current
     * value is null.
     * 
     * @see #uninstallDefaults
     * @see #installUI
     */
    @Override
    protected void installDefaults() {
        JTextComponent editor = getComponent();
        PaletteLookAndFeel plaf = PaletteLookAndFeel.getInstance();

        String prefix = getPropertyPrefix();
        Font f = editor.getFont();
        if ((f == null) || (f instanceof UIResource)) {
            editor.setFont(plaf.getFont(prefix + ".font"));
        }

        Color bg = editor.getBackground();
        if ((bg == null) || (bg instanceof UIResource)) {
            editor.setBackground(plaf.getColor(prefix + ".background"));
        }

        Color fg = editor.getForeground();
        if ((fg == null) || (fg instanceof UIResource)) {
            editor.setForeground(plaf.getColor(prefix + ".foreground"));
        }

        Color color = editor.getCaretColor();
        if ((color == null) || (color instanceof UIResource)) {
            editor.setCaretColor(plaf.getColor(prefix + ".caretForeground"));
        }

        Color s = editor.getSelectionColor();
        if ((s == null) || (s instanceof UIResource)) {
            editor.setSelectionColor(plaf.getColor(prefix + ".selectionBackground"));
        }

        Color sfg = editor.getSelectedTextColor();
        if ((sfg == null) || (sfg instanceof UIResource)) {
            editor.setSelectedTextColor(plaf.getColor(prefix + ".selectionForeground"));
        }

        Color dfg = editor.getDisabledTextColor();
        if ((dfg == null) || (dfg instanceof UIResource)) {
            editor.setDisabledTextColor(plaf.getColor(prefix + ".inactiveForeground"));
        }

        Border b = editor.getBorder();
        if ((b == null) || (b instanceof UIResource)) {
            editor.setBorder(plaf.getBorder(prefix + ".border"));
        }

        Insets margin = editor.getMargin();
        if (margin == null || margin instanceof UIResource) {
            editor.setMargin(plaf.getInsets(prefix + ".margin"));
        }

        errorIndicatorForeground = plaf.getColor(prefix+".errorIndicatorForeground");

        editor.setOpaque(plaf.getBoolean(prefix + ".opaque"));

    }

    @Override
    protected void paintSafely(Graphics gr) {
        Graphics2D g = (Graphics2D) gr;

        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_FRACTIONALMETRICS, RenderingHints.VALUE_FRACTIONALMETRICS_ON);
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);

        super.paintSafely(g);
    }

    @Override
    public void paintBackground(Graphics g) {
        JTextComponent c = getComponent();
        if (c.getBorder() instanceof BackdropBorder) {
            BackdropBorder bb = (BackdropBorder) c.getBorder();
            bb.getBackdropBorder().paintBorder(c, g, 0, 0, c.getWidth(), c.getHeight());
        } else {
            super.paintBackground(g);
        }
    }
}
