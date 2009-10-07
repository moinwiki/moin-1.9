/*
 * @(#)SheetEvent.java
 *
 * Copyright (c) 1996-2006 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

package org.jhotdraw.gui.event;

import org.jhotdraw.gui.*;
import java.util.*;
import javax.swing.*;
import org.jhotdraw.gui.JSheet;
/**
 * SheetEvent.
 *
 * @author  Werner Randelshofer
 * @version $Id: SheetEvent.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class SheetEvent extends EventObject {
    private JComponent pane;
    private int option;
    private Object value;
    private Object inputValue;
    
    /**
     * Creates a new instance.
     */
    public SheetEvent(JSheet source) {
        super(source);
    }
    /**
     * Creates a new instance.
     */
    public SheetEvent(JSheet source, JFileChooser fileChooser, int option, Object value) {
        super(source);
        this.pane = fileChooser;
        this.option = option;
        this.value = value;
    }
    /**
     * Creates a new instance.
     */
    public SheetEvent(JSheet source, JOptionPane optionPane, int option, Object value, Object inputValue) {
        super(source);
        this.pane = optionPane;
        this.option = option;
        this.value = value;
        this.inputValue = inputValue;
    }
    
    /**
     * Returns the pane on the sheet. This is either a JFileChooser or a
     * JOptionPane.
     */
    public JComponent getPane() {
        return pane;
    }
    /**
     * Returns the JFileChooser pane on the sheet.
     */
    public JFileChooser getFileChooser() {
        return (JFileChooser) pane;
    }
    /**
     * Returns the JOptionPane pane on the sheet.
     */
    public JOptionPane getOptionPane() {
        return (JOptionPane) pane;
    }
    /**
     * Returns the option that the JFileChooser or JOptionPane returned.
     */
    public int getOption() {
        return option;
    }
    /**
     * Returns the value that the JFileChooser or JOptionPane returned.
     */
    public Object getValue() {
        return value;
    }    
    /**
     * Returns the input value that the JOptionPane returned, if it wants input.
     */
    public Object getInputValue() {
        return inputValue;
    }    
}
