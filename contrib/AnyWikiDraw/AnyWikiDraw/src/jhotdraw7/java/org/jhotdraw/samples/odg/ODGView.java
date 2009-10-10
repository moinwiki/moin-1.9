/*
 * @(#)ODGView.java
 *
 * Copyright (c) 1996-2007 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 *
 */
package org.jhotdraw.samples.odg;

import java.awt.image.BufferedImage;
import java.awt.print.Pageable;
import java.util.HashMap;
import java.util.LinkedList;
import org.jhotdraw.gui.*;
import org.jhotdraw.samples.odg.io.ODGInputFormat;
import org.jhotdraw.samples.svg.figures.*;
import org.jhotdraw.samples.svg.io.*;
import org.jhotdraw.undo.*;
import org.jhotdraw.util.*;
import java.awt.*;
import java.beans.*;
import java.io.*;
import java.lang.reflect.*;
import javax.swing.*;
import javax.swing.border.*;
import org.jhotdraw.app.*;
import org.jhotdraw.app.action.*;
import org.jhotdraw.draw.*;
import org.jhotdraw.draw.action.*;

/**
 * A view for ODG drawings.
 *
 * @author Werner Randelshofer
 * @version $Id: ODGView.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ODGView extends AbstractView implements ExportableView {
    public final static String GRID_VISIBLE_PROPERTY = "gridVisible";
    protected JFileChooser exportChooser;
    
    /**
     * Each ODGView uses its own undo redo manager.
     * This allows for undoing and redoing actions per view.
     */
    private UndoRedoManager undo;
    
    /**
     * Depending on the type of an application, there may be one editor per
     * view, or a single shared editor for all views.
     */
    private DrawingEditor editor;
    
    private HashMap<javax.swing.filechooser.FileFilter, InputFormat> fileFilterInputFormatMap;
    private HashMap<javax.swing.filechooser.FileFilter, OutputFormat> fileFilterOutputFormatMap;
    
    private GridConstrainer visibleConstrainer = new GridConstrainer(10, 10);
    private GridConstrainer invisibleConstrainer = new GridConstrainer(1, 1);
    /**
     * Creates a new view.
     */
    public ODGView() {
    }
    
    /**
     * Initializes the view.
     */
    public void init() {
        super.init();
        
        initComponents();
        
        JPanel zoomButtonPanel = new JPanel(new BorderLayout());
        scrollPane.setLayout(new PlacardScrollPaneLayout());
        scrollPane.setBorder(new EmptyBorder(0,0,0,0));
        
        setEditor(new DefaultDrawingEditor());
        undo = new UndoRedoManager();
        view.setDrawing(createDrawing());
        view.getDrawing().addUndoableEditListener(undo);
        initActions();
        undo.addPropertyChangeListener(new PropertyChangeListener() {
            public void propertyChange(PropertyChangeEvent evt) {
                setHasUnsavedChanges(undo.hasSignificantEdits());
            }
        });
        
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
        
        JPanel placardPanel = new JPanel(new BorderLayout());
        javax.swing.AbstractButton pButton;
        pButton = ButtonFactory.createZoomButton(view);
        pButton.putClientProperty("Quaqua.Button.style","placard");
        pButton.putClientProperty("Quaqua.Component.visualMargin",new Insets(0,0,0,0));
        pButton.setFont(UIManager.getFont("SmallSystemFont"));
        placardPanel.add(pButton, BorderLayout.WEST);
        pButton = ButtonFactory.createToggleGridButton(view);
        pButton.putClientProperty("Quaqua.Button.style","placard");
        pButton.putClientProperty("Quaqua.Component.visualMargin",new Insets(0,0,0,0));
        pButton.setFont(UIManager.getFont("SmallSystemFont"));
        labels.configureToolBarButton(pButton, "view.toggleGrid.placard");
        placardPanel.add(pButton, BorderLayout.EAST);
        scrollPane.add(placardPanel, JScrollPane.LOWER_LEFT_CORNER);
        
        propertiesPanel.setVisible(preferences.getBoolean("propertiesPanelVisible", false));
        propertiesPanel.setView(view);
    }
    
    /**
     * Creates a new Drawing for this view.
     */
    protected Drawing createDrawing() {
        Drawing drawing = new ODGDrawing();
        LinkedList<InputFormat> inputFormats = new LinkedList<InputFormat>();
        inputFormats.add(new ODGInputFormat());
        inputFormats.add(new ImageInputFormat(new SVGImageFigure()));
        inputFormats.add(new ImageInputFormat(new SVGImageFigure(), "JPG","Joint Photographics Experts Group (JPEG)", "jpg", BufferedImage.TYPE_INT_RGB));
        inputFormats.add(new ImageInputFormat(new SVGImageFigure(), "GIF","Graphics Interchange Format (GIF)", "gif", BufferedImage.TYPE_INT_ARGB));
        inputFormats.add(new TextInputFormat(new SVGTextFigure()));
        drawing.setInputFormats(inputFormats);
        LinkedList<OutputFormat> outputFormats = new LinkedList<OutputFormat>();
        outputFormats.add(new SVGOutputFormat());
        outputFormats.add(new SVGZOutputFormat());
        outputFormats.add(new ImageOutputFormat());
        outputFormats.add(new ImageOutputFormat("JPG","Joint Photographics Experts Group (JPEG)", "jpg", BufferedImage.TYPE_INT_RGB));
        outputFormats.add(new ImageOutputFormat("BMP","Windows Bitmap (BMP)", "bmp", BufferedImage.TYPE_BYTE_INDEXED));
        outputFormats.add(new ImageMapOutputFormat());
        drawing.setOutputFormats(outputFormats);
        return drawing;
    }
    /**
     * Creates a Pageable object for printing the view.
     */
    public Pageable createPageable() {
        return new DrawingPageable(view.getDrawing());
        
    }
    public DrawingEditor getEditor() {
        return editor;
    }
    public void setEditor(DrawingEditor newValue) {
        DrawingEditor oldValue = editor;
        if (oldValue != null) {
            oldValue.remove(view);
        }
        editor = newValue;
        propertiesPanel.setEditor(editor);
        if (newValue != null) {
            newValue.add(view);
        }
    }
    
    /**
     * Initializes view specific actions.
     */
    private void initActions() {
        putAction(UndoAction.ID, undo.getUndoAction());
        putAction(RedoAction.ID, undo.getRedoAction());
    }
    protected void setHasUnsavedChanges(boolean newValue) {
        super.setHasUnsavedChanges(newValue);
        undo.setHasSignificantEdits(newValue);
    }
    
    /**
     * Writes the view to the specified file.
     */
    public void write(File f) throws IOException {
        OutputStream out = null;
        try {
            out = new BufferedOutputStream(new FileOutputStream(f));
            new SVGOutputFormat().write(f, view.getDrawing());
        } finally {
            if (out != null) out.close();
        }
    }
    
    /**
     * Reads the view from the specified file.
     */
    public void read(File f) throws IOException {
        try {
            JFileChooser fc = getOpenChooser();
            
            final Drawing drawing = createDrawing();
            InputFormat sf = fileFilterInputFormatMap.get(fc.getFileFilter());
            if (sf == null) {
                sf = drawing.getInputFormats().get(0);
            }
            sf.read(f, drawing, true);
            
            System.out.println("ODCView read("+f+") drawing.childCount="+drawing.getChildCount());
            
            SwingUtilities.invokeAndWait(new Runnable() { public void run() {
                view.getDrawing().removeUndoableEditListener(undo);
                view.setDrawing(drawing);
                view.getDrawing().addUndoableEditListener(undo);
                undo.discardAllEdits();
            }});
        } catch (InterruptedException e) {
            InternalError error = new InternalError();
            e.initCause(e);
            throw error;
        } catch (InvocationTargetException e) {
            InternalError error = new InternalError();
            error.initCause(e);
            throw error;
        }
    }
    
    
    public Drawing getDrawing() {
        return view.getDrawing();
    }
    
    public void setEnabled(boolean newValue) {
        view.setEnabled(newValue);
        super.setEnabled(newValue);
    }
    
    public void setPropertiesPanelVisible(boolean newValue) {
        boolean oldValue = propertiesPanel.isVisible();
        propertiesPanel.setVisible(newValue);
        firePropertyChange("propertiesPanelVisible", oldValue, newValue);
        preferences.putBoolean("propertiesPanelVisible", newValue);
        validate();
    }
    public boolean isPropertiesPanelVisible() {
        return propertiesPanel.isVisible();
    }
    public boolean isGridVisible() {
        return view.isConstrainerVisible();
    }
    public void setGridVisible(boolean newValue) {
        boolean oldValue = isGridVisible();
        view.setConstrainerVisible(newValue);
        firePropertyChange(GRID_VISIBLE_PROPERTY, oldValue, newValue);
    }
    public double getScaleFactor() {
        return view.getScaleFactor();
    }
    public void setScaleFactor(double newValue) {
        double oldValue = getScaleFactor();
        view.setScaleFactor(newValue);
        firePropertyChange("scaleFactor", oldValue, newValue);
    }
    
    
    /**
     * Clears the view.
     */
    public void clear() {
        final Drawing newDrawing = createDrawing();
        try {
            SwingUtilities.invokeAndWait(new Runnable() {
                public void run() {
                    view.getDrawing().removeUndoableEditListener(undo);
                    view.setDrawing(newDrawing);
                    view.getDrawing().addUndoableEditListener(undo);
                    undo.discardAllEdits();
                }
            });
        } catch (InvocationTargetException ex) {
            ex.printStackTrace();
        } catch (InterruptedException ex) {
            ex.printStackTrace();
        }
    }
    
    @Override protected JFileChooser createOpenChooser() {
        final JFileChooser c = new JFileChooser();
        fileFilterInputFormatMap = new HashMap<javax.swing.filechooser.FileFilter,InputFormat>();
        javax.swing.filechooser.FileFilter firstFF = null;
        for (InputFormat format : view.getDrawing().getInputFormats()) {
            javax.swing.filechooser.FileFilter ff = format.getFileFilter();
            if (firstFF == null) {
                firstFF = ff;
            }
            fileFilterInputFormatMap.put(ff, format);
            c.addChoosableFileFilter(ff);
        }
        c.setFileFilter(firstFF);
        c.addPropertyChangeListener(new PropertyChangeListener() {
            public void propertyChange(PropertyChangeEvent evt) {
                if (evt.getPropertyName().equals("fileFilterChanged")) {
                    InputFormat inputFormat = fileFilterInputFormatMap.get(evt.getNewValue());
                    c.setAccessory((inputFormat == null) ? null : inputFormat.getInputFormatAccessory());
                }
            }
        });
        if (preferences != null) {
            c.setSelectedFile(new File(preferences.get("projectFile", System.getProperty("user.home"))));
        }
        
        return c;
    }
    @Override protected JFileChooser createSaveChooser() {
        JFileChooser c = new JFileChooser();
        
        fileFilterOutputFormatMap = new HashMap<javax.swing.filechooser.FileFilter,OutputFormat>();
        //  c.addChoosableFileFilter(new ExtensionFileFilter("SVG Drawing","svg"));
        for (OutputFormat format : view.getDrawing().getOutputFormats()) {
            javax.swing.filechooser.FileFilter ff = format.getFileFilter();
            fileFilterOutputFormatMap.put(ff, format);
            c.addChoosableFileFilter(ff);
            break; // only add the first file filter
        }
        if (preferences != null) {
            c.setSelectedFile(new File(preferences.get("projectFile", System.getProperty("user.home"))));
        }
        
        return c;
    }
    @Override
    public boolean canSaveTo(File file) {
        return file.getName().endsWith(".odg");
    }
    protected JFileChooser createExportChooser() {
        JFileChooser c = new JFileChooser();
        
        fileFilterOutputFormatMap = new HashMap<javax.swing.filechooser.FileFilter,OutputFormat>();
        //  c.addChoosableFileFilter(new ExtensionFileFilter("SVG Drawing","svg"));
        javax.swing.filechooser.FileFilter currentFilter = null;
        for (OutputFormat format : view.getDrawing().getOutputFormats()) {
            javax.swing.filechooser.FileFilter ff = format.getFileFilter();
            fileFilterOutputFormatMap.put(ff, format);
            c.addChoosableFileFilter(ff);
            if (ff.getDescription().equals(preferences.get("viewExportFormat",""))) {
                currentFilter = ff;
            }
        }
        if (currentFilter != null) {
            c.setFileFilter(currentFilter);
        }
        c.setSelectedFile(new File(preferences.get("viewExportFile", System.getProperty("user.home"))));
        
        return c;
    }
    
    /** This method is called from within the constructor to
     * initialize the form.
     * WARNING: Do NOT modify this code. The content of this method is
     * always regenerated by the Form Editor.
     */
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents() {

        scrollPane = new javax.swing.JScrollPane();
        view = new org.jhotdraw.draw.DefaultDrawingView();
        propertiesPanel = new org.jhotdraw.samples.odg.ODGPropertiesPanel();

        setLayout(new java.awt.BorderLayout());

        scrollPane.setHorizontalScrollBarPolicy(javax.swing.ScrollPaneConstants.HORIZONTAL_SCROLLBAR_ALWAYS);
        scrollPane.setVerticalScrollBarPolicy(javax.swing.ScrollPaneConstants.VERTICAL_SCROLLBAR_ALWAYS);
        scrollPane.setViewportView(view);

        add(scrollPane, java.awt.BorderLayout.CENTER);
        add(propertiesPanel, java.awt.BorderLayout.SOUTH);
    }// </editor-fold>//GEN-END:initComponents
    
    public JFileChooser getExportChooser() {
        if (exportChooser == null) {
            exportChooser = createExportChooser();
        }
        return exportChooser;
    }
    
    public void export(File f, javax.swing.filechooser.FileFilter filter, Component accessory) throws IOException {
        
        OutputFormat format = fileFilterOutputFormatMap.get(filter);
        
        if (! f.getName().endsWith("."+format.getFileExtension())) {
            f = new File(f.getPath()+"."+format.getFileExtension());
        }
        
        format.write(f, view.getDrawing());
        
        preferences.put("viewExportFile", f.getPath());
        preferences.put("viewExportFormat", filter.getDescription());
    }
    
    
    // Variables declaration - do not modify//GEN-BEGIN:variables
    private org.jhotdraw.samples.odg.ODGPropertiesPanel propertiesPanel;
    private javax.swing.JScrollPane scrollPane;
    private org.jhotdraw.draw.DefaultDrawingView view;
    // End of variables declaration//GEN-END:variables
    
}
