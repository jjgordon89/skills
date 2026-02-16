package cmd

import (
	"fmt"
	"log"
	"os"
	"strconv"
	"text/tabwriter"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

// Wantlist defines the structure for the entire wantlist response from Discogs.
type Wantlist struct {
	Wants []Want `json:"wants"`
}

// Want represents a single item in the user's wantlist.
type Want struct {
	ID               int              `json:"id"`
	BasicInformation BasicInformation `json:"basic_information"`
}

// BasicInformation contains the core details about a release.
type BasicInformation struct {
	Artists []Artist `json:"artists"`
	Title   string   `json:"title"`
	Year    int      `json:"year"`
}

// wantlistCmd represents the base command for wantlist operations.
// It doesn't do anything on its own but serves as an entry point for subcommands.
var wantlistCmd = &cobra.Command{
	Use:   "wantlist",
	Short: "Manage your Discogs wantlist",
	Long:  `Provides subcommands to list, add, or remove items from your wantlist.`,
}

// wantlistListCmd handles listing all items in the wantlist.
var wantlistListCmd = &cobra.Command{
	Use:   "list",
	Short: "List items in your wantlist",
	Run: func(cmd *cobra.Command, args []string) {
		// Ensure the user is configured
		username := viper.GetString("username")
		if username == "" {
			log.Fatalf("Error: 'username' not set in config file. Please run 'discogs-cli config set'.")
		}

		// Construct the API request URL
		url := fmt.Sprintf("https://api.discogs.com/users/%s/wants", username)
		var wantlist Wantlist

		// Perform the API request
		err := wantlistRequest("GET", url, &wantlist)
		if err != nil {
			log.Fatalf("Error fetching wantlist: %v", err)
		}

		if len(wantlist.Wants) == 0 {
			fmt.Println("Wantlist is empty.")
			return
		}

		// Format the output into a table
		w := new(tabwriter.Writer)
		w.Init(os.Stdout, 0, 8, 2, ' ', 0)
		fmt.Fprintln(w, "ID\tARTIST\tTITLE\tYEAR")
		fmt.Fprintln(w, "--\t------\t-----\t----")

		for _, want := range wantlist.Wants {
			artist := "Unknown Artist"
			if len(want.BasicInformation.Artists) > 0 {
				artist = want.BasicInformation.Artists[0].Name
			}
			idStr := strconv.Itoa(want.ID)
			yearStr := strconv.Itoa(want.BasicInformation.Year)
			fmt.Fprintf(w, "%s\t%s\t%s\t%s\n", idStr, artist, want.BasicInformation.Title, yearStr)
		}
		w.Flush()
	},
}

// wantlistAddCmd handles adding a release to the wantlist.
var wantlistAddCmd = &cobra.Command{
	Use:   "add [release_id]",
	Short: "Add a release to your wantlist",
	Args:  cobra.ExactArgs(1), // Ensures exactly one argument (the release ID) is provided
	Run: func(cmd *cobra.Command, args []string) {
		username := viper.GetString("username")
		if username == "" {
			log.Fatalf("Error: 'username' not set in config file. Please run 'discogs-cli config set'.")
		}

		releaseID := args[0]
		url := fmt.Sprintf("https://api.discogs.com/users/%s/wants/%s", username, releaseID)

		// Perform a PUT request to add the item
		err := wantlistRequest("PUT", url, nil)
		if err != nil {
			log.Fatalf("Error adding to wantlist: %v", err)
		}

		fmt.Printf("Successfully added release %s to wantlist.\n", releaseID)
	},
}

// wantlistRemoveCmd handles removing a release from the wantlist.
var wantlistRemoveCmd = &cobra.Command{
	Use:   "remove [release_id]",
	Short: "Remove a release from your wantlist",
	Args:  cobra.ExactArgs(1), // Ensures exactly one argument (the release ID) is provided
	Run: func(cmd *cobra.Command, args []string) {
		username := viper.GetString("username")
		if username == "" {
			log.Fatalf("Error: 'username' not set in config file. Please run 'discogs-cli config set'.")
		}

		releaseID := args[0]
		url := fmt.Sprintf("https://api.discogs.com/users/%s/wants/%s", username, releaseID)

		// Perform a DELETE request to remove the item
		err := wantlistRequest("DELETE", url, nil)
		if err != nil {
			log.Fatalf("Error removing from wantlist: %v", err)
		}

		fmt.Printf("Successfully removed release %s from wantlist.\n", releaseID)
	},
}

// init registers the wantlist command and its subcommands with the root command.
func init() {
	rootCmd.AddCommand(wantlistCmd)
	wantlistCmd.AddCommand(wantlistListCmd)
	wantlistCmd.AddCommand(wantlistAddCmd)
	wantlistCmd.AddCommand(wantlistRemoveCmd)
}
