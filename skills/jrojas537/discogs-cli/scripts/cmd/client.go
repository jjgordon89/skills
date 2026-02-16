
package cmd

import (
	"log"

	"github.com/irlndts/go-discogs"
	"github.com/spf13/viper"
)

func newDiscogsClient() discogs.Discogs {
	token := viper.GetString("token")
	username := viper.GetString("username")

	if token == "" || username == "" {
		log.Fatalf("Error: 'token' and 'username' not set in config file. Please run 'discogs-cli config set'.")
	}

	client, err := discogs.New(&discogs.Options{
		UserAgent: "OpenClawDiscogsSkill/1.1-Beta",
		Token:     token,
	})
	if err != nil {
		log.Fatalf("Error creating Discogs client: %v", err)
	}
	return client
}
