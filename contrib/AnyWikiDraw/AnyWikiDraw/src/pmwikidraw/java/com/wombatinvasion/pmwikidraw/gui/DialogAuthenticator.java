/*
 * Created on 04-Dec-2004
 *
 * TODO To change the template for this generated file go to
 * Window - Preferences - Java - Code Style - Code Templates
 * 
 * From: O'Reilly Java Network Programming.
 */
package com.wombatinvasion.pmwikidraw.gui;

import java.net.*;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;


/**
 * @author bob
 *
 * TODO To change the template for this generated type comment go to
 * Window - Preferences - Java - Code Style - Code Templates
 */
public class DialogAuthenticator extends Authenticator {
	
	public class CancelResponse implements ActionListener {

		/* (non-Javadoc)
		 * @see java.awt.event.ActionListener#actionPerformed(java.awt.event.ActionEvent)
		 */
		public void actionPerformed(ActionEvent arg0) {
			passwordDialog.hide();
			passwordField.setText("");
			response = null;
		}

	}

	public class OKResponse implements ActionListener {

		/* (non-Javadoc)
		 * @see java.awt.event.ActionListener#actionPerformed(java.awt.event.ActionEvent)
		 */
		public void actionPerformed(ActionEvent arg0) {
			passwordDialog.hide();
			
			char[] password = passwordField.getPassword();
			String username = usernameField.getText();
			System.out.println(username+ ","+ new String(password));
			passwordField.setText("");
			response = new PasswordAuthentication(username, password);
		}
	}
	
	private JDialog passwordDialog;
	private JLabel mainLabel = new JLabel("Please enter username and password: ");
	private JLabel userLabel = new JLabel("Username: ");
	private JLabel passwordLabel = new JLabel("Password: ");
	private JTextField usernameField = new JTextField(20);
	private JPasswordField passwordField = new JPasswordField(20);
	private JButton okButton = new JButton("OK");
	private JButton cancelButton = new JButton("Cancel");
	
	public DialogAuthenticator() {
		this("", new JFrame());
	}
	
	public DialogAuthenticator(String username) {
		this(username, new JFrame());
	}
	
	public DialogAuthenticator(String username, JFrame parent) {
		
		this.passwordDialog = new JDialog(parent, true);
		Container pane = passwordDialog.getContentPane();
		pane.setLayout(new GridLayout(4,1));
		pane.add(mainLabel);
		JPanel p2 = new JPanel();
		p2.add(userLabel);
		p2.add(usernameField);
		usernameField.setText(username);
		pane.add(p2);
		
		JPanel p3 = new JPanel();
		p3.add(passwordLabel);
		p3.add(passwordField);
		pane.add(p3);
		
		JPanel p4 = new JPanel();
		p4.add(okButton);
		p4.add(cancelButton);
		pane.add(p4);
		passwordDialog.pack();
		
		ActionListener al = new OKResponse();
		okButton.addActionListener(al);
		usernameField.addActionListener(al);
		passwordField.addActionListener(al);
		cancelButton.addActionListener(new CancelResponse());
	}
	
	private void show() {
		
		String prompt = this.getRequestingPrompt();
		if ( prompt == null ) {
			String site = this.getRequestingSite().getHostName();
			String protocol = this.getRequestingProtocol();
			int port = this.getRequestingPort();
			
			if ( site != null && protocol != null) {
				prompt = protocol + "://"+ site;
				if(port >0) 
					  prompt += ":" + port;
			}
			else {
				prompt = "";
			}
		}
		
		mainLabel.setText("Please enter username and password for "+ prompt + ": ");
		passwordDialog.pack();
		passwordDialog.setVisible(true);
	}
	
	PasswordAuthentication response = null;
/* (non-Javadoc)
 * @see java.net.Authenticator#getPasswordAuthentication()
 */
protected PasswordAuthentication getPasswordAuthentication() {
	this.show();
	return this.response;
}	
	
}
