#! /usr/bin/python3
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from AHF_HeadFixer import AHF_HeadFixer
from time import sleep
from _thread import start_new_thread
from random import random
from AHF_ContactCheck_BeamBreak import setAngle

class AHF_HeadFixer_PWM(AHF_HeadFixer, metaclass = ABCMeta):
    """
    Abstract class for PWM-based head fixers for servo motors. As long as your subclass maps your PWM range onto
    the appropriate pulse width for the servo, you should be good to go.
    """
    hasLevels = True
    numLevels =8
    defaultReleasePosition = 933
    defaultFixedPosition = 685
    defaultTightnessHeadFix = 1

    @staticmethod
    @abstractmethod
    def config_user_get(starterDict = {}):
        starterDict.update(AHF_HeadFixer.config_user_get(starterDict))
        servoReleasedPosition = starterDict.get('servoReleasedPosition', AHF_HeadFixer_PWM.defaultReleasePosition)
        response = input("Set Servo Released Position(0-4095: currently %d): " % servoReleasedPosition)
        if response != '':
            servoReleasedPosition = int(response)
        servoFixedPosition = starterDict.get('servoFixedPosition', AHF_HeadFixer_PWM.defaultFixedPosition)
        response = input("Set Servo Fixed Position(0-4095: currently %d): " % servoFixedPosition)
        if response != '':
            servoFixedPosition = int(response)
        starterDict.update({'servoReleasedPosition' : servoReleasedPosition, 'servoFixedPosition' : servoFixedPosition})
        return starterDict

    def config_user_subject_get(self,starterDict = {}):
        tightnessHeadFix = starterDict.get('tightnessHeadFix', AHF_HeadFixer_PWM.defaultTightnessHeadFix)
        response = input(
            'Enter percentage(0 to 1) of head-fix tightness(0 equals release, 1 equals full head-fix)\n'
            ' values below 0.5 might allow the mouse to leave the tunnel , currently {:.2f}: '.format(tightnessHeadFix))
        if response != '':
            tightnessHeadFix = float(response)
        starterDict.update({'tightnessHeadFix': tightnessHeadFix})
        return super().config_user_subject_get(starterDict)

    def config_subject_get(self, starterDict={}):
        tightnessHeadFix = starterDict.get('tightnessHeadFix', AHF_HeadFixer_PWM.defaultTightnessHeadFix)
        starterDict.update({'tightnessHeadFix': tightnessHeadFix})
        return super().config_subject_get(starterDict)

    def individualSettings(self, starterDict={}):
        """
        copies servo fixed position to dictionary - there is no reason to have different released positions per subject
        TO DO: add multiple headfixing levels, maybe progression based on resdults
        """
        starterDict.update({'servoFixedPosition' : self.servoFixedPosition})
        return starterDict


    @abstractmethod
    def setup(self):
        super().setup()
        self.servoReleasedPosition = self.settingsDict.get('servoReleasedPosition')
        self.servoFixedPosition = self.settingsDict.get('servoFixedPosition')
        if self.__class__.hasLevels:
            self.servoIncrement =(self.servoFixedPosition - self.servoReleasedPosition)/self.numLevels

    def setdown(self):
        super().setdown()
        self.setPWM((self.servoFixedPosition + self.servoReleasedPosition)/2)

    def calculate_steps(self,individualDict):
        percentage = individualDict.get('servoFixedPosition', self.servoFixedPosition)
        percentage = min(max(percentage,0),1)
        target_pos = int(self.servoReleasedPosition +(self.servoFixedPosition-self.servoReleasedPosition)*percentage)
        return target_pos

    def fixMouse(self, thisTag, resultsDict = {}, individualDict= {}):
        if thisTag == 0:
            return False
        self.task.isFixTrial = self.task.Subjects.get(thisTag).get("HeadFixer").get("propHeadFix") > random()
        hasContact = False
        if self.task.isFixTrial:
            if self.waitForMouse(thisTag): # contact was made
                self.setPWM(self.calculate_steps(individualDict))
                sleep(0.5)
                hasContact = self.task.contact
                if not hasContact: # tried to fix and failed
                    self.setPWM(self.servoReleasedPosition)
                self.hasMouseLog(hasContact, self.task.isFixTrial, thisTag, resultsDict)
        else: # noFix trial, wait for contact and return
            self.hasMouseLog(hasContact, self.task.isFixTrial, thisTag, resultsDict)
            if self.waitForMouse(thisTag) and not AHF_HeadFixer.isChecking:
                start_new_thread(self.isFixedCheck,())
                return True
            return False
        return hasContact
    # TODO get rid of resultsdict

    def releaseMouse(self, thisTag, resultsDict = {}, settingsDict= {}):
        self.setPWM(self.servoReleasedPosition)
        super().releaseMouse(thisTag, resultsDict, settingsDict)
        setAngle(0)

    # each PWM subclass must implement its own code to set the pulse width
    @abstractmethod
    def setPWM(self, servoPosition):
        pass


    # Head-Fixer hardware test overwritten to just modify fixed and released servo positions, other settings not likely to change
    def hardwareTest(self):
        print('servo moving to Head-Fixed position for 3 seconds')
        #Fix and release have extra overhead, so replace with position
        #self.fixMouse()
        self.setPWM(self.servoFixedPosition)
        sleep(3)
        print('servo moving to Released position')
        self.setPWM(self.servoReleasedPosition)
        inputStr= input('Do you want to change fixed position(currently %d) or released position(currently %d)? ' %(self.servoFixedPosition ,self.servoReleasedPosition))
        if inputStr[0] == 'y' or inputStr[0] == "Y":
            self.settingsDict = AHF_HeadFixer_PWM.config_user_get(self.settingsDict)
            self.servoReleasedPosition = self.settingsDict.get('servoReleasedPosition')
            self.servoFixedPosition = self.settingsDict.get('servoFixedPosition')
        repeatedTest = input('Do you want to start a fatigue test? (y/n)')
        if repeatedTest[0].lower() == 'y':
            while True:
                try:
                    self.setPWM(self.servoFixedPosition)
                    sleep(3)
                    print('servo moving to Released position')
                    self.setPWM(self.servoReleasedPosition)
                    sleep(3)
                except KeyboardInterrupt:
                    break


