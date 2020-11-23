package com.podcast.rawdata;

import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.logging.Logger;

public class SpeakerDiarisation {

	public static List<File> getAllFiles(String directoryName) {
		File directory = new File(directoryName);

		List<File> resultList = new ArrayList<File>();

		// get all the files from a directory
		File[] fList = directory.listFiles();
		resultList.addAll(Arrays.asList(fList));
		for (File file : fList) {
			if (file.isDirectory()) {
				resultList.addAll(getAllFiles(file.getAbsolutePath()));
			}
		}
		return resultList;
	}

	public static void main(String[] args) throws Exception {
		Logger cmRootLogger = Logger.getLogger("default.config");
		cmRootLogger.setLevel(java.util.logging.Level.OFF);
		String conFile = System.getProperty("java.util.logging.config.file");
		if (conFile == null) {
			System.setProperty("java.util.logging.config.file", "ignoreAllSphinx4LoggingOutput");
		}
		ExecutorService executorService = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());

		String inPath = args[0];
		List<File> listOfFiles = getAllFiles(inPath);
		int i = 1;
		for (File file : listOfFiles) {
			if (file.isFile() && file.getName().endsWith(".wav")) {
				// start new thread for diarisation
				executorService.execute(new SplitAudioBySpeakers(file, i));
				i++;
			}
		}
		executorService.shutdown();
	}
}