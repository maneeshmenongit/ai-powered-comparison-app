/**
 * Splash Screen & Onboarding Manager
 * Handles first-time user experience
 */

class SplashOnboardingManager {
    constructor() {
        this.currentScreen = 0;
        this.totalScreens = 3;
        this.hasSeenOnboarding = this.checkOnboardingStatus();
    }

    /**
     * Check if user has seen onboarding before
     */
    checkOnboardingStatus() {
        return localStorage.getItem('hopwise_onboarding_completed') === 'true';
    }

    /**
     * Mark onboarding as completed
     */
    completeOnboarding() {
        localStorage.setItem('hopwise_onboarding_completed', 'true');
    }

    /**
     * Initialize splash screen and onboarding flow
     */
    initialize() {
        // Show splash screen immediately
        this.showSplashScreen();

        // After 2.5 seconds, hide splash and show onboarding (or go to app)
        setTimeout(() => {
            this.hideSplashScreen();

            if (!this.hasSeenOnboarding) {
                this.showOnboarding();
            } else {
                this.goToApp();
            }
        }, 2500);
    }

    /**
     * Show splash screen
     */
    showSplashScreen() {
        const splash = document.getElementById('splash-screen');
        if (splash) {
            splash.style.display = 'flex';
        }
    }

    /**
     * Hide splash screen with fade-out animation
     */
    hideSplashScreen() {
        const splash = document.getElementById('splash-screen');
        if (splash) {
            splash.classList.add('fade-out');
            setTimeout(() => {
                splash.style.display = 'none';
            }, 500);
        }
    }

    /**
     * Show onboarding screens
     */
    showOnboarding() {
        const container = document.getElementById('onboarding-container');
        if (container) {
            container.classList.add('active');
            this.showScreen(0);
        }
    }

    /**
     * Hide onboarding container
     */
    hideOnboarding() {
        const container = document.getElementById('onboarding-container');
        if (container) {
            container.classList.remove('active');
        }
    }

    /**
     * Show specific onboarding screen
     */
    showScreen(index) {
        this.currentScreen = index;

        // Hide all screens
        const screens = document.querySelectorAll('.onboarding-screen');
        screens.forEach(screen => screen.classList.remove('active'));

        // Show current screen
        const currentScreen = document.getElementById(`onboarding-screen-${index + 1}`);
        if (currentScreen) {
            currentScreen.classList.add('active');
        }

        // Update dots
        this.updateDots();

        // Update skip button visibility (hide on last screen)
        const skipBtn = document.getElementById('skip-btn');
        if (skipBtn) {
            if (index === this.totalScreens - 1) {
                skipBtn.classList.add('hidden');
            } else {
                skipBtn.classList.remove('hidden');
            }
        }
    }

    /**
     * Update progress dots
     */
    updateDots() {
        const dots = document.querySelectorAll('.dot');
        dots.forEach((dot, index) => {
            if (index === this.currentScreen) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
    }

    /**
     * Go to next screen
     */
    nextScreen() {
        if (this.currentScreen < this.totalScreens - 1) {
            this.showScreen(this.currentScreen + 1);
        } else {
            // Last screen - complete onboarding
            this.finishOnboarding();
        }
    }

    /**
     * Skip onboarding
     */
    skipOnboarding() {
        this.finishOnboarding();
    }

    /**
     * Finish onboarding and go to app
     */
    finishOnboarding() {
        this.completeOnboarding();
        this.hideOnboarding();
        this.goToApp();
    }

    /**
     * Go to main app
     */
    goToApp() {
        // Show the main app content
        const app = document.getElementById('app');
        if (app) {
            app.style.display = 'block';
        }

        // Initialize the main app if needed
        if (window.Hopwise && window.Hopwise.init) {
            window.Hopwise.init();
        }
    }

    /**
     * Show sign in page
     */
    showSignIn() {
        this.finishOnboarding();
        // Navigate to login/signup page
        if (window.Hopwise && window.Hopwise.navigateTo) {
            window.Hopwise.navigateTo('profile');
        }
    }

    /**
     * Reset onboarding (for testing)
     */
    resetOnboarding() {
        localStorage.removeItem('hopwise_onboarding_completed');
        this.hasSeenOnboarding = false;
        console.log('Onboarding reset. Refresh the page to see it again.');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.splashOnboarding = new SplashOnboardingManager();
    window.splashOnboarding.initialize();
});

// Expose reset function for testing
window.resetOnboarding = () => {
    if (window.splashOnboarding) {
        window.splashOnboarding.resetOnboarding();
    }
};
