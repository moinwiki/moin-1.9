/*
 * @(#)CharacterSetAccessory.java
 *
 * Copyright (c) 2005 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and
 * contributors of the JHotDraw project ("the copyright holders").
 * You may not use, copy or modify this software, except in
 * accordance with the license agreement you entered into with
 * the copyright holders. For details see accompanying license terms.
 */

package org.jhotdraw.samples.teddy;

import org.jhotdraw.gui.*;
import java.nio.charset.*;
import javax.swing.*;
import java.util.*;
import java.util.prefs.*;
import org.jhotdraw.util.prefs.PreferencesUtil;
/**
 * CharacterSetAccessory.
 *
 * @author Werner Randelshofer
 * @version $Id: CharacterSetAccessory.java 529 2009-06-08 21:12:23Z rawcoder $
 */
public class CharacterSetAccessory extends javax.swing.JPanel {
    private final static Preferences prefs = PreferencesUtil.userNodeForPackage(TeddyView.class);
    private static Object[] availableCharSets;
    
    /** Creates a new instance. */
    public CharacterSetAccessory() {
        if (UIManager.getLookAndFeel().getID().toLowerCase().equals("aqua")) {
        initComponents();
        } else {
        initComponentsWin();
        }
        
        String selectedItem = prefs.get("characterSet","UTF-8");
        charSetCombo.setModel(new DefaultComboBoxModel(new String[] { selectedItem }));
        charSetCombo.setSelectedItem(selectedItem);
        charSetCombo.setEnabled(false);
        fetchAvailableCharSets();
        
        String lineSeparator = prefs.get("lineSeparator","\n");
        if (lineSeparator.equals("\r")) {
            lineSepCombo.setSelectedIndex(0);
        } else if (lineSeparator.equals("\n")) {
            lineSepCombo.setSelectedIndex(1);
        } else if (lineSeparator.equals("\r\n")) {
            lineSepCombo.setSelectedIndex(2);
        }
    }
    
    public void fetchAvailableCharSets() {
        if (availableCharSets == null) {
            new Worker() {
                public Object construct() {
                    SortedMap<String,Charset> sm = Charset.availableCharsets();
                    LinkedList<String> list = new LinkedList<String>();
                    for (String key : sm.keySet()) {
                        if (! key.startsWith("x-")) {
                            list.add(key);
                        }
                    }
                    availableCharSets = list.toArray();
                    Arrays.sort(availableCharSets);
                    return null;
                }
                public void finished(Object value) {
                    Object selectedItem = charSetCombo.getSelectedItem();
                    charSetCombo.setModel(new DefaultComboBoxModel(availableCharSets));
                    charSetCombo.setSelectedItem(selectedItem);
                    charSetCombo.setEnabled(true);
                }
                
            }.start();
        } else {
            Object selectedItem = charSetCombo.getSelectedItem();
            charSetCombo.setModel(new DefaultComboBoxModel(availableCharSets));
            charSetCombo.setSelectedItem(selectedItem);
            charSetCombo.setEnabled(true);
        }
    }
    
    public String getCharacterSet() {
        prefs.put("characterSet", (String) charSetCombo.getSelectedItem());
        return (String) charSetCombo.getSelectedItem();
    }
    public String getLineSeparator() {
        String lineSeparator;
        switch (charSetCombo.getSelectedIndex()) {
            case 0 : default : lineSeparator = "\n"; break;
            case 1 : lineSeparator = "\r"; break;
            case 2 : lineSeparator = "\r\n"; break;
        }
        prefs.put("lineSeparator", lineSeparator);
        return lineSeparator;
    }
    
    /** This method is called from within the constructor to
     * initialize the form.
     * WARNING: Do NOT modify this code. The content of this method is
     * always regenerated by the Form Editor.
     */
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents() {

        charSetLabel = new javax.swing.JLabel();
        charSetCombo = new javax.swing.JComboBox();
        lineSepLabel = new javax.swing.JLabel();
        lineSepCombo = new javax.swing.JComboBox();

        setBorder(javax.swing.BorderFactory.createTitledBorder(""));

        charSetLabel.setText("Character Set:");

        charSetCombo.setModel(new javax.swing.DefaultComboBoxModel(new String[] { "Item 1", "Item 2", "Item 3", "Item 4" }));

        lineSepLabel.setText("Line Separator:");

        lineSepCombo.setModel(new javax.swing.DefaultComboBoxModel(new String[] { "CR", "LF", "CR LF" }));

        org.jdesktop.layout.GroupLayout layout = new org.jdesktop.layout.GroupLayout(this);
        this.setLayout(layout);
        layout.setHorizontalGroup(
            layout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
            .add(layout.createSequentialGroup()
                .add(charSetLabel)
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                .add(charSetCombo, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.UNRELATED)
                .add(lineSepLabel)
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                .add(lineSepCombo, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
        );
        layout.setVerticalGroup(
            layout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
            .add(charSetLabel)
            .add(charSetCombo, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE)
            .add(lineSepLabel)
            .add(lineSepCombo, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE)
        );
    }// </editor-fold>//GEN-END:initComponents
    
    private void initComponentsWin() {
        charSetLabel = new javax.swing.JLabel();
        charSetCombo = new javax.swing.JComboBox();
        lineSepLabel = new javax.swing.JLabel();
        lineSepCombo = new javax.swing.JComboBox();
        
        setBorder(javax.swing.BorderFactory.createTitledBorder(""));
        charSetLabel.setText("Character Set:");
        
        charSetCombo.setModel(new javax.swing.DefaultComboBoxModel(new String[] { "Item 1", "Item 2", "Item 3", "Item 4" }));
        
        lineSepLabel.setText("Line Separator:");
        
        lineSepCombo.setModel(new javax.swing.DefaultComboBoxModel(new String[] { "CR", "LF", "CR LF" }));
        
        org.jdesktop.layout.GroupLayout layout = new org.jdesktop.layout.GroupLayout(this);
        this.setLayout(layout);
        layout.setHorizontalGroup(
                layout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
                .add(charSetLabel)
                .add(charSetCombo, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE)
                .add(lineSepLabel)
                .add(lineSepCombo, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE)
                );
        layout.setVerticalGroup(
                layout.createSequentialGroup()
                .add(charSetLabel)
                .add(charSetCombo, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.UNRELATED)
                .add(lineSepLabel)
                .add(lineSepCombo, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE)
                );
    }
    
    // Variables declaration - do not modify//GEN-BEGIN:variables
    public javax.swing.JComboBox charSetCombo;
    public javax.swing.JLabel charSetLabel;
    public javax.swing.JComboBox lineSepCombo;
    public javax.swing.JLabel lineSepLabel;
    // End of variables declaration//GEN-END:variables
    
}
