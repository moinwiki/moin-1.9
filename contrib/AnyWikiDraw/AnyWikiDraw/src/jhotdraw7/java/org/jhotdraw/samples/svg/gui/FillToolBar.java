/*
 * @(#)FillToolBar.java
 *
 * Copyright (c) 2007-2008 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.samples.svg.gui;

import org.jhotdraw.gui.event.SelectionComponentRepainter;
import org.jhotdraw.gui.event.FigureAttributeEditorHandler;
import org.jhotdraw.gui.event.SelectionComponentDisplayer;
import org.jhotdraw.text.JavaNumberFormatter;
import javax.swing.border.*;
import org.jhotdraw.gui.*;
import org.jhotdraw.util.*;
import java.awt.*;
import java.util.HashMap;
import java.util.Map;
import javax.swing.*;
import javax.swing.plaf.SliderUI;
import org.jhotdraw.draw.*;
import org.jhotdraw.draw.action.*;
import org.jhotdraw.gui.plaf.palette.*;
import org.jhotdraw.text.ColorFormatter;
import static org.jhotdraw.samples.svg.SVGAttributeKeys.*;

/**
 * FillToolBar.
 *
 * @author Werner Randelshofer
 * @version $Id: FillToolBar.java 541 2009-07-04 14:24:31Z rawcoder $
 */
public class FillToolBar extends AbstractToolBar {

    private SelectionComponentDisplayer displayer;

    /** Creates new instance. */
    public FillToolBar() {
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.samples.svg.Labels");
        setName(labels.getString(getID() + ".toolbar"));
        setDisclosureStateCount(3);
    }

    @Override
    public void setEditor(DrawingEditor newValue) {
        DrawingEditor oldValue = getEditor();
        if (displayer != null) {
            displayer.dispose();
            displayer = null;
        }
        super.setEditor(newValue);
        if (newValue != null) {
            displayer = new SelectionComponentDisplayer(editor, this);
        }
    }

    @Override
    protected JComponent createDisclosedComponent(int state) {
        JPanel p = null;

        switch (state) {
            case 1:
                 {
                    p = new JPanel();
                    p.setOpaque(false);
                    p.setBorder(new EmptyBorder(5, 5, 5, 8));
                    ResourceBundleUtil drawLabels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
                    ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.samples.svg.Labels");
                    GridBagLayout layout = new GridBagLayout();
                    p.setLayout(layout);
                    GridBagConstraints gbc;
                    AbstractButton btn;

                    // Fill color
                    Map<AttributeKey, Object> defaultAttributes = new HashMap<AttributeKey, Object>();
                    FILL_GRADIENT.set(defaultAttributes, null);
                    btn = ButtonFactory.createSelectionColorButton(editor,
                            FILL_COLOR, ButtonFactory.HSV_COLORS, ButtonFactory.HSV_COLORS_COLUMN_COUNT,
                            "attribute.fillColor", drawLabels, defaultAttributes, new Rectangle(3, 3, 10, 10), disposables);
                    btn.setUI((PaletteButtonUI) PaletteButtonUI.createUI(btn));
                    ((JPopupButton) btn).setAction(null, null);
                    gbc = new GridBagConstraints();
                    gbc.gridx = 0;
                    gbc.gridwidth = 2;
                    gbc.anchor = GridBagConstraints.FIRST_LINE_START;
                    p.add(btn, gbc);

                    // Opacity slider
                    JPopupButton opacityPopupButton = new JPopupButton();
                    JAttributeSlider opacitySlider = new JAttributeSlider(JSlider.VERTICAL, 0, 100, 100);
                    opacityPopupButton.add(opacitySlider);
                    labels.configureToolBarButton(opacityPopupButton, "attribute.fillOpacity");
                    opacityPopupButton.setUI((PaletteButtonUI) PaletteButtonUI.createUI(opacityPopupButton));
                    opacityPopupButton.setIcon(
                            new SelectionOpacityIcon(editor, FILL_OPACITY, FILL_COLOR, null, Images.createImage(getClass(),labels.getString("attribute.fillOpacity.icon")),
                            new Rectangle(5, 5, 6, 6), new Rectangle(4, 4, 7, 7)));
                    opacityPopupButton.setPopupAnchor(SOUTH_EAST);
                    disposables.add(new SelectionComponentRepainter(editor, opacityPopupButton));
                    gbc = new GridBagConstraints();
                    gbc.gridx = 0;
                    gbc.anchor = GridBagConstraints.FIRST_LINE_START;
                    gbc.weighty = 1f;
                    gbc.insets = new Insets(3, 0, 0, 0);
                    p.add(opacityPopupButton, gbc);
                    opacitySlider.setUI((SliderUI) PaletteSliderUI.createUI(opacitySlider));
                    opacitySlider.setScaleFactor(100d);
                    disposables.add(new FigureAttributeEditorHandler<Double>(FILL_OPACITY, opacitySlider, editor));
                }
                break;

            case 2:
                 {
                    p = new JPanel();
                    p.setOpaque(false);

                    JPanel p1 = new JPanel(new GridBagLayout());
                    JPanel p2 = new JPanel(new GridBagLayout());
                    JPanel p3 = new JPanel(new GridBagLayout());
                    p1.setOpaque(false);
                    p2.setOpaque(false);
                    p3.setOpaque(false);

                    p.setBorder(new EmptyBorder(5, 5, 5, 8));
                    p.removeAll();

                    ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.samples.svg.Labels");
                    GridBagLayout layout = new GridBagLayout();
                    p.setLayout(layout);
                    GridBagConstraints gbc;
                    AbstractButton btn;

                    // Fill color field and button
                    Map<AttributeKey, Object> defaultAttributes = new HashMap<AttributeKey, Object>();
                    FILL_GRADIENT.set(defaultAttributes, null);
                    JAttributeTextField<Color> colorField = new JAttributeTextField<Color>();
                    colorField.setColumns(7);
                    colorField.setToolTipText(labels.getString("attribute.fillColor.toolTipText"));
                    colorField.putClientProperty("Palette.Component.segmentPosition", "first");
                    colorField.setUI((PaletteFormattedTextFieldUI) PaletteFormattedTextFieldUI.createUI(colorField));
                    colorField.setFormatterFactory(ColorFormatter.createFormatterFactory());
                    colorField.setHorizontalAlignment(JTextField.LEFT);
                    disposables.add(new FigureAttributeEditorHandler<Color>(FILL_COLOR, defaultAttributes, colorField, editor, true));
                    gbc = new GridBagConstraints();
                    gbc.gridx = 0;
                    gbc.fill = GridBagConstraints.HORIZONTAL;
                    gbc.anchor = GridBagConstraints.FIRST_LINE_START;
                    p1.add(colorField, gbc);
                    btn = ButtonFactory.createSelectionColorButton(editor,
                            FILL_COLOR, ButtonFactory.HSV_COLORS, ButtonFactory.HSV_COLORS_COLUMN_COUNT,
                            "attribute.fillColor", labels, defaultAttributes, new Rectangle(3, 3, 10, 10), disposables);
                    btn.setUI((PaletteButtonUI) PaletteButtonUI.createUI(btn));
                    ((JPopupButton) btn).setAction(null, null);
                    gbc = new GridBagConstraints();
                    gbc.gridx = 1;
                    gbc.gridwidth = 2;
                    gbc.anchor = GridBagConstraints.FIRST_LINE_START;
                    p1.add(btn, gbc);

                    // Opacity field with slider
                    JAttributeTextField<Double> opacityField = new JAttributeTextField<Double>();
                    opacityField.setColumns(3);
                    opacityField.setToolTipText(labels.getString("attribute.fillOpacity.toolTipText"));
                    opacityField.putClientProperty("Palette.Component.segmentPosition", "first");
                    opacityField.setUI((PaletteFormattedTextFieldUI) PaletteFormattedTextFieldUI.createUI(opacityField));
                    opacityField.setFormatterFactory(JavaNumberFormatter.createFormatterFactory(0d, 1d, 100d));
                    opacityField.setHorizontalAlignment(JTextField.LEFT);
                    disposables.add(new FigureAttributeEditorHandler<Double>(FILL_OPACITY, opacityField, editor));
                    gbc = new GridBagConstraints();
                    gbc.gridx = 0;
                    gbc.insets = new Insets(3, 0, 0, 0);
                    gbc.fill = GridBagConstraints.HORIZONTAL;
                    gbc.anchor = GridBagConstraints.FIRST_LINE_START;
                    p2.add(opacityField, gbc);
                    JPopupButton opacityPopupButton = new JPopupButton();
                    JAttributeSlider opacitySlider = new JAttributeSlider(JSlider.VERTICAL, 0, 100, 100);
                    opacityPopupButton.add(opacitySlider);
                    labels.configureToolBarButton(opacityPopupButton, "attribute.fillOpacity");
                    opacityPopupButton.setUI((PaletteButtonUI) PaletteButtonUI.createUI(opacityPopupButton));
                    opacityPopupButton.setPopupAnchor(SOUTH_EAST);
                    opacityPopupButton.setIcon(
                            new SelectionOpacityIcon(editor, FILL_OPACITY, FILL_COLOR, null, Images.createImage(getClass(),labels.getString("attribute.fillOpacity.icon")),
                            new Rectangle(5, 5, 6, 6), new Rectangle(4, 4, 7, 7)));
                    opacityPopupButton.setPopupAnchor(SOUTH_EAST);
                    disposables.add(new SelectionComponentRepainter(editor, opacityPopupButton));
                    gbc = new GridBagConstraints();
                    gbc.gridx = 1;
                    gbc.anchor = GridBagConstraints.FIRST_LINE_START;
                    gbc.weighty = 1f;
                    gbc.insets = new Insets(3, 0, 0, 0);
                    p2.add(opacityPopupButton, gbc);
                    opacitySlider.setUI((SliderUI) PaletteSliderUI.createUI(opacitySlider));
                    opacitySlider.setScaleFactor(100d);
                    disposables.add(new FigureAttributeEditorHandler<Double>(FILL_OPACITY, opacitySlider, editor));

                    // Add horizontal strips
                    gbc = new GridBagConstraints();
                    gbc.gridy = 0;
                    gbc.anchor = GridBagConstraints.FIRST_LINE_START;
                    p.add(p1, gbc);
                    gbc = new GridBagConstraints();
                    gbc.gridy = 1;
                    gbc.anchor = GridBagConstraints.FIRST_LINE_START;
                    p.add(p2, gbc);
                    gbc = new GridBagConstraints();
                    gbc.gridy = 2;
                    gbc.weighty = 1f;
                    gbc.anchor = GridBagConstraints.FIRST_LINE_START;
                    p.add(p3, gbc);
                }
                break;
        }
        return p;
    }

    @Override
    protected String getID() {
        return "fill";
    }
    @Override
    protected int getDefaultDisclosureState() {
        return 1;
    }


    /** This method is called from within the constructor to
     * initialize the form.
     * WARNING: Do NOT modify this code. The content of this method is
     * always regenerated by the Form Editor.
     */
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents() {

        setOpaque(false);
    }// </editor-fold>//GEN-END:initComponents
    // Variables declaration - do not modify//GEN-BEGIN:variables
    // End of variables declaration//GEN-END:variables
}
